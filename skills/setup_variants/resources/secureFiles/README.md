# Environment Configuration Files

**⚠️ SECURITY WARNING: These files contain sensitive information and should NEVER be committed to version control!**

## What are these files?

These JSON files contain environment-specific configuration for different deployment environments (dev, stg, prd). They are loaded at build time using Flutter's `--dart-define-from-file` feature.

## File Structure

Each environment folder should contain:
- `environment-configs.json` - Main environment configuration

## How to use

These files are automatically loaded by:
1. VS Code launch configurations (`.vscode/launch.json`)
2. Build scripts (`scripts/buildApk.sh`, `scripts/buildIPA.sh`, etc.)

## Important Notes

1. **Never commit these files to git** - They should be in `.gitignore`
2. **Store securely** - Use encrypted storage or secret management tools
3. **Share carefully** - Only share with authorized team members through secure channels
4. **Update regularly** - Keep API keys and secrets rotated

## Template

See the example files in each folder for the required structure.
