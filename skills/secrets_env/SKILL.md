---
name: secrets_env
description: Use this skill when the project needs to build but the secureFiles/ directory is missing. Detects whether provisioning already happened, decodes the SECURE_FILES environment variable as a fallback, and tells the user exactly what to run if neither is available.
---


**Scenario**: You (the Agent) need to build the project, but `secureFiles/` is missing.

---

## ⚡ Step-by-Step Procedure

### 1. Detect Provisioning
Check if the setup script handled it already:
```bash
ls -d secureFiles/
# or use the alias
verify-secrets
```
If present, you are good to go.

### 2. Manual Decoding (Fallback)
If `secureFiles/` is missing but the environment variable `SECURE_FILES` is present, you can manually decode it:
```bash
echo "$SECURE_FILES" | base64 -d | tar -xz
```

### 3. Requesting from User (The "Jules" way)
If neither exists, request the base64 string from the user.
> **Prompt**: "I noticed the `secureFiles/` directory is missing and `SECURE_FILES` is not set. Could you please run `bash scripts/secrets_ops.sh encode` on your local machine and provide the output so I can configure the environment variables?"

---

## 🔧 Local Tool for User
Tell the user to use:
- `bash scripts/secrets_ops.sh encode`
