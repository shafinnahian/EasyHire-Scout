#!/usr/bin/env python3
"""
Test script for Skill Matcher Service - All Three Tiers

Tests each tier independently and combined:
- Tier 1: Exact matching (canonical names and variants)
- Tier 2: Fuzzy matching (typos and variations)
- Tier 3: LLM matching (abbreviations and semantic understanding)

Usage:
    python scripts/test_skill_matcher_tiers.py
    python scripts/test_skill_matcher_tiers.py --no-llm  # Skip Tier 3
    python scripts/test_skill_matcher_tiers.py --tier1-only
    python scripts/test_skill_matcher_tiers.py --tier2-only
    python scripts/test_skill_matcher_tiers.py --tier3-only
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from easyhire_scout.database import SessionLocal
from easyhire_scout.skills import SkillMatcherService
from easyhire_scout.models import Skill


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(raw_input: str, skill_name: str | None, confidence: float, tier: str, needs_review: bool):
    """Print formatted match result."""
    review_flag = "⚠️" if needs_review else "✓"
    confidence_str = f"{confidence:.2f}"
    
    # Color coding based on tier
    tier_emoji = {
        "exact": "🎯",
        "fuzzy": "🔍",
        "llm": "🤖",
        "none": "❌"
    }
    
    emoji = tier_emoji.get(tier, "?")
    
    if skill_name:
        print(f"{review_flag} {emoji} {raw_input:20s} → {skill_name:25s} "
              f"(confidence: {confidence_str}, tier: {tier})")
    else:
        print(f"{review_flag} {emoji} {raw_input:20s} → NO MATCH "
              f"(confidence: {confidence_str}, tier: {tier})")


def test_tier1_exact_matches(db):
    """Test Tier 1: Exact matching on canonical names and variants."""
    print_header("TIER 1: EXACT MATCHING (Canonical Names & Variants)")
    
    test_skills = [
        "Python",           # Exact canonical name
        "JavaScript",       # Exact canonical name
        "React",            # Exact canonical name
        "py",               # Known variant of Python
        "js",               # Known variant of JavaScript
        "reactjs",          # Known variant of React
        "k8s",              # Known variant of Kubernetes
        "postgres",         # Known variant of PostgreSQL
    ]
    
    print(f"\nTesting {len(test_skills)} skills that should match in Tier 1...")
    print("(These should all be instant <1ms matches)\n")
    
    results = SkillMatcherService.match_skills(db, test_skills, use_llm=False)
    
    tier1_count = 0
    for result in results:
        print_result(
            result.raw_input,
            result.skill_name,
            result.confidence,
            result.tier_used,
            result.needs_review
        )
        if result.tier_used == "exact":
            tier1_count += 1
    
    print(f"\n📊 Tier 1 Results: {tier1_count}/{len(test_skills)} matched in Tier 1")
    return tier1_count == len(test_skills)


def test_tier2_fuzzy_matches(db):
    """Test Tier 2: Fuzzy matching for typos and variations."""
    print_header("TIER 2: FUZZY MATCHING (Typos & Variations)")
    
    test_skills = [
        "Pythoon",          # Typo in Python
        "Javascrpt",        # Typo in JavaScript
        "Reactjs",          # Variation of React (if not in variants)
        "Postgre SQL",      # Spacing variation
        "Kuberntes",        # Typo in Kubernetes
        "Docekr",           # Typo in Docker
    ]
    
    print(f"\nTesting {len(test_skills)} skills with typos/variations...")
    print("(These should match via fuzzy matching <10ms)\n")
    
    results = SkillMatcherService.match_skills(db, test_skills, use_llm=False)
    
    tier2_count = 0
    for result in results:
        print_result(
            result.raw_input,
            result.skill_name,
            result.confidence,
            result.tier_used,
            result.needs_review
        )
        if result.tier_used == "fuzzy":
            tier2_count += 1
    
    print(f"\n📊 Tier 2 Results: {tier2_count}/{len(test_skills)} matched in Tier 2")
    return tier2_count > 0


def test_tier3_llm_matches(db):
    """Test Tier 3: LLM semantic matching."""
    print_header("TIER 3: LLM MATCHING (Semantic Understanding)")
    
    test_skills = [
        "ML",               # Abbreviation for Machine Learning
        "AI",               # Abbreviation for Artificial Intelligence
        "DL",               # Abbreviation for Deep Learning
        "k8s",              # Slang for Kubernetes (if not in variants)
        "React.js",         # Framework variation
        "Node",             # Short for Node.js
        "Postgres",         # Short for PostgreSQL
        "Mongo",            # Short for MongoDB
    ]
    
    print(f"\nTesting {len(test_skills)} skills requiring semantic understanding...")
    print("(These may use LLM if not matched in Tier 1/2, ~1-3s each)\n")
    
    results = SkillMatcherService.match_skills(db, test_skills, use_llm=True)
    
    tier3_count = 0
    matched_count = 0
    for result in results:
        print_result(
            result.raw_input,
            result.skill_name,
            result.confidence,
            result.tier_used,
            result.needs_review
        )
        if result.tier_used == "llm":
            tier3_count += 1
        if result.skill_id:
            matched_count += 1
    
    print(f"\n📊 Tier 3 Results: {tier3_count} used LLM, {matched_count}/{len(test_skills)} total matched")
    return matched_count > 0


def test_no_matches(db):
    """Test skills that should not match anything."""
    print_header("NO MATCH TEST (Invalid/Unknown Skills)")
    
    test_skills = [
        "XYZ123",           # Nonsense
        "FooBar",           # Not a real skill
        "RandomTech",       # Made up
        "SkillDoesNotExist", # Clearly fake
    ]
    
    print(f"\nTesting {len(test_skills)} invalid skills...")
    print("(These should all return no match)\n")
    
    results = SkillMatcherService.match_skills(db, test_skills, use_llm=True)
    
    no_match_count = 0
    for result in results:
        print_result(
            result.raw_input,
            result.skill_name,
            result.confidence,
            result.tier_used,
            result.needs_review
        )
        if result.tier_used == "none":
            no_match_count += 1
    
    print(f"\n📊 No Match Results: {no_match_count}/{len(test_skills)} correctly returned no match")
    return no_match_count == len(test_skills)


def test_combined_batch(db):
    """Test a realistic batch with mixed tier requirements."""
    print_header("COMBINED BATCH TEST (All Tiers)")
    
    test_skills = [
        # Tier 1 candidates
        "Python", "JavaScript", "React",
        # Tier 2 candidates
        "Pythoon", "Reactjs",
        # Tier 3 candidates
        "ML", "k8s", "AI",
        # No match candidates
        "FakeSkill123"
    ]
    
    print(f"\nTesting {len(test_skills)} mixed skills in one batch...")
    print("(Should cascade through tiers efficiently)\n")
    
    results = SkillMatcherService.match_skills(db, test_skills, use_llm=True)
    
    tier_stats = {"exact": 0, "fuzzy": 0, "llm": 0, "none": 0}
    matched_count = 0
    
    for result in results:
        print_result(
            result.raw_input,
            result.skill_name,
            result.confidence,
            result.tier_used,
            result.needs_review
        )
        tier_stats[result.tier_used] += 1
        if result.skill_id:
            matched_count += 1
    
    print(f"\n📊 Combined Results:")
    print(f"   Total processed: {len(test_skills)}")
    print(f"   Matched: {matched_count}/{len(test_skills)}")
    print(f"   Tier 1 (exact): {tier_stats['exact']}")
    print(f"   Tier 2 (fuzzy): {tier_stats['fuzzy']}")
    print(f"   Tier 3 (llm): {tier_stats['llm']}")
    print(f"   No match: {tier_stats['none']}")
    
    return matched_count > 0


def check_prerequisites(db):
    """Check if system is ready for testing."""
    print_header("PREREQUISITES CHECK")
    
    # Check skills in database
    skill_count = db.query(Skill).count()
    print(f"✓ Skills in database: {skill_count}")
    
    if skill_count == 0:
        print("\n❌ ERROR: No skills in database!")
        print("   Run: python scripts/seed_skills.py")
        return False
    
    # Check API key
    from easyhire_scout.core.config import settings
    has_api_key = bool(settings.DEEPSEEK_API_KEY)
    print(f"{'✓' if has_api_key else '⚠️'} DeepSeek API key: {'Configured' if has_api_key else 'Not configured'}")
    
    if not has_api_key:
        print("   ⚠️  Tier 3 (LLM) tests will be skipped")
    
    # Check LLM enabled
    llm_enabled = settings.ENABLE_LLM_MATCHING
    print(f"{'✓' if llm_enabled else '⚠️'} LLM matching: {'Enabled' if llm_enabled else 'Disabled'}")
    
    print("\n✅ System ready for testing")
    return True


def main():
    """Run all tests."""
    parser = argparse.ArgumentParser(description="Test Skill Matcher Service")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM tests")
    parser.add_argument("--tier1-only", action="store_true", help="Test Tier 1 only")
    parser.add_argument("--tier2-only", action="store_true", help="Test Tier 2 only")
    parser.add_argument("--tier3-only", action="store_true", help="Test Tier 3 only")
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("  SKILL MATCHER SERVICE - TIER TESTING")
    print("=" * 70)
    
    db = SessionLocal()
    
    try:
        # Check prerequisites
        if not check_prerequisites(db):
            return 1
        
        results = {}
        
        # Run selected tests
        if args.tier1_only:
            results["tier1"] = test_tier1_exact_matches(db)
        elif args.tier2_only:
            results["tier2"] = test_tier2_fuzzy_matches(db)
        elif args.tier3_only:
            if args.no_llm:
                print("\n⚠️  Cannot run Tier 3 tests with --no-llm flag")
                return 1
            results["tier3"] = test_tier3_llm_matches(db)
        else:
            # Run all tests
            results["tier1"] = test_tier1_exact_matches(db)
            results["tier2"] = test_tier2_fuzzy_matches(db)
            
            if not args.no_llm:
                results["tier3"] = test_tier3_llm_matches(db)
            else:
                print("\n⚠️  Skipping Tier 3 (LLM) tests (--no-llm flag)")
            
            results["no_match"] = test_no_matches(db)
            results["combined"] = test_combined_batch(db)
        
        # Summary
        print_header("TEST SUMMARY")
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, passed_test in results.items():
            status = "✅ PASSED" if passed_test else "❌ FAILED"
            print(f"{status}: {test_name}")
        
        print(f"\n{'✅' if passed == total else '⚠️'} Overall: {passed}/{total} test suites passed")
        
        if passed == total:
            print("\n🎉 All tests passed! Skill matcher is working correctly.")
            return 0
        else:
            print("\n⚠️  Some tests failed. Check output above for details.")
            return 1
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
