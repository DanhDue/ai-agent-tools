# Signing Configuration

⚠️ **IMPORTANT: Never commit this folder to version control!**

## Files in this folder

### debug.keystore
Default Android debug keystore for development and staging builds.
- **Password**: `android`
- **Key Alias**: `androiddebugkey`
- **Key Password**: `android`

### keystore.properties (for production)
Properties file for production keystore configuration.

**Required format:**
```properties
storeFile=your-release.keystore
storePassword=your-store-password
keyAlias=your-key-alias
keyPassword=your-key-password
```

### your-release.keystore (for production)
Your production release keystore file.

---

## How to Generate Production Keystore

```bash
keytool -genkey -v -keystore your-release.keystore \
  -alias your-key-alias \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000
```

Then create `keystore.properties` with the passwords you set.

---

## Security Notes

1. **Never commit** these files to git (already in `.gitignore`)
2. **Backup** your production keystore securely
3. **Store passwords** in a password manager
4. **Share with team** through secure channels only

---

## File Structure

```
secureFiles/signing/
├── debug.keystore          (Development/Staging signing)
├── keystore.properties     (Production keystore config)
└── your-release.keystore   (Production signing)
```
