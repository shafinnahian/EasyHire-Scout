# Security Guidelines - Skill Matcher Service

## 🔐 API Key Security (CRITICAL)

### ✅ What We Do (Secure)

1. **API Key Stored in `.env` File**
   ```env
   # .env (NOT committed to git)
   LLM_API_KEY=sk-a9a73eefc94248049b1838e302172d4c
   ```

2. **`.env` in `.gitignore`**
   ```gitignore
   # .gitignore
   .env
   .env.local
   ```

3. **Fail-Fast Validation**
   ```python
   # easyhire_scout/core/config.py
   class Settings(BaseSettings):
       LLM_API_KEY: str = Field(
           description="DeepSeek API key (REQUIRED - from .env)"
       )
   
   settings = Settings()  # Crashes if LLM_API_KEY missing
   ```

4. **`.env.example` Committed (Template Only)**
   ```env
   # .env.example (safe to commit)
   LLM_API_KEY=sk-placeholder-get-your-key-from-deepseek-dashboard
   ```

### ❌ What We NEVER Do (Insecure)

1. **❌ NEVER Hardcode API Keys**
   ```python
   # BAD - NEVER DO THIS
   API_KEY = "sk-a9a73eefc94248049b1838e302172d4c"
   ```

2. **❌ NEVER Commit `.env` to Git**
   ```bash
   # BAD - NEVER DO THIS
   git add .env
   git commit -m "Add config"
   ```

3. **❌ NEVER Log API Keys**
   ```python
   # BAD - NEVER DO THIS
   logger.info(f"Using API key: {settings.LLM_API_KEY}")
   ```

4. **❌ NEVER Pass Keys in URLs**
   ```python
   # BAD - NEVER DO THIS
   url = f"https://api.example.com?key={api_key}"
   ```

5. **❌ NEVER Store Keys in Code/Comments**
   ```python
   # BAD - NEVER DO THIS
   # My API key: sk-a9a73eefc94248049b1838e302172d4c
   ```

## 🛡️ Security Checklist

Before deploying or committing code:

- [ ] API key is in `.env` file
- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` has placeholder values only
- [ ] No API keys in code files
- [ ] No API keys in logs
- [ ] No API keys in error messages
- [ ] No API keys in URLs
- [ ] No API keys in comments

## 🔍 How to Verify Security

### Check 1: Verify `.env` is Ignored

```bash
# Should show .env in .gitignore
grep "^\.env$" .gitignore

# Should show nothing (not tracked)
git ls-files | grep "^\.env$"
```

### Check 2: Search for Hardcoded Keys

```bash
# Search for potential API keys in code
grep -r "sk-[a-zA-Z0-9]" easyhire_scout/ --exclude-dir=.git

# Should only find references in:
# - .env (not tracked)
# - .env.example (placeholder only)
# - Documentation (examples only)
```

### Check 3: Verify Config Loading

```python
# Test that config loads from .env
from easyhire_scout.core.config import settings

# This should work (loads from .env)
print(f"API key loaded: {settings.LLM_API_KEY[:10]}...")

# This should crash if .env is missing
# (fail-fast behavior is GOOD)
```

## 🚨 What to Do If Key is Exposed

If you accidentally commit an API key:

### 1. Immediately Revoke the Key

```bash
# Go to DeepSeek dashboard
# https://platform.deepseek.com/api_keys
# Click "Revoke" on the exposed key
```

### 2. Generate New Key

```bash
# Generate new key in dashboard
# Update .env with new key
echo "LLM_API_KEY=sk-new-key-here" > .env
```

### 3. Remove from Git History

```bash
# Remove .env from all commits (if accidentally committed)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch .env" \
  --prune-empty --tag-name-filter cat -- --all

# Force push (WARNING: rewrites history)
git push origin --force --all
```

### 4. Notify Team

- Inform team that key was exposed
- Ensure everyone updates their `.env`
- Review security practices

## 🔒 Production Deployment

### Environment Variables (Recommended)

For production, use environment variables instead of `.env` files:

```bash
# Docker
docker run -e LLM_API_KEY=sk-prod-key-here ...

# Kubernetes
kubectl create secret generic llm-api-key \
  --from-literal=LLM_API_KEY=sk-prod-key-here

# AWS ECS
# Set environment variables in task definition

# Heroku
heroku config:set LLM_API_KEY=sk-prod-key-here
```

### Secret Management (Best Practice)

Use a secret management service:

- **AWS Secrets Manager**
- **HashiCorp Vault**
- **Azure Key Vault**
- **Google Secret Manager**

Example with AWS Secrets Manager:

```python
import boto3

def get_api_key():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='llm-api-key')
    return response['SecretString']
```

## 📋 Security Best Practices

### 1. Principle of Least Privilege

- Only give API key to services that need it
- Use separate keys for dev/staging/prod
- Rotate keys regularly (every 90 days)

### 2. Monitoring

- Monitor API usage for anomalies
- Set up alerts for unusual activity
- Track API costs

### 3. Access Control

- Limit who can access production keys
- Use role-based access control (RBAC)
- Audit key access logs

### 4. Code Reviews

- Always review `.gitignore` changes
- Check for hardcoded secrets in PRs
- Use automated secret scanning tools

## 🛠️ Tools for Secret Scanning

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Add to .pre-commit-config.yaml
repos:
  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.4.0
    hooks:
      - id: detect-secrets
```

### GitHub Secret Scanning

GitHub automatically scans for exposed secrets:
- Enable in repository settings
- Receives alerts for exposed keys
- Automatically revokes some keys

### GitGuardian

```bash
# Install GitGuardian CLI
pip install ggshield

# Scan repository
ggshield secret scan repo .
```

## ✅ Current Security Status

**EasyHire Scout Skill Matcher Service:**

✅ API key loaded from `.env` (secure)  
✅ `.env` in `.gitignore` (not tracked)  
✅ `.env.example` has placeholders only  
✅ Fail-fast validation (crashes if missing)  
✅ No hardcoded keys in code  
✅ No keys in logs or error messages  
✅ Property accessor for backward compatibility  

**Security Level:** 🟢 **SECURE**

## 📞 Security Contact

If you discover a security vulnerability:

1. **DO NOT** open a public issue
2. **DO NOT** commit the fix publicly
3. Contact the security team privately
4. Wait for acknowledgment before disclosure

---

**Remember:** Security is everyone's responsibility. When in doubt, ask!