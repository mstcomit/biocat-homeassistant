# WaterCryst BIOCAT Integration Repository Setup

This guide helps you set up your own GitHub repository for the WaterCryst BIOCAT Home Assistant integration to make it installable via HACS.

## Quick Setup

1. **Fork or Download** this repository
2. **Create a new GitHub repository** with the files
3. **Update the following files** with your GitHub username:

### Files to Update

Replace `YOUR_USERNAME` with your actual GitHub username in these files:

#### `info.md`
```markdown
- **Integration Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/biocat/issues)
- **Documentation**: [Full README](https://github.com/YOUR_USERNAME/biocat/blob/main/README.md)
```

#### `README.md`
```markdown
4. Add this repository URL: `https://github.com/YOUR_USERNAME/biocat`
```

#### `custom_components/watercryst/manifest.json`
```json
{
  "documentation": "https://github.com/YOUR_USERNAME/biocat",
  "issue_tracker": "https://github.com/YOUR_USERNAME/biocat/issues"
}
```

#### `HACS_INSTALLATION.md`
```markdown
- **Repository**: `https://github.com/YOUR_USERNAME/biocat`
```

### Badge URLs
Update all badge URLs in README.md and info.md:
- `YOUR_USERNAME/biocat` → `yourusername/biocat`

## Repository Settings

### Releases
1. Create your first release:
   ```bash
   git tag v1.0.0
   git push origin main --tags
   ```

2. Go to GitHub → Releases → Create Release
   - Tag: `v1.0.0`
   - Title: `v1.0.0`
   - Description: "Initial release"

### Repository Description
Set your repository description to:
```
Home Assistant integration for WaterCryst BIOCAT water treatment and leakage protection systems
```

### Topics
Add these topics to your repository:
- `home-assistant`
- `hacs`
- `watercryst`
- `biocat`
- `integration`
- `water-treatment`
- `leakage-protection`

## HACS Installation

Once your repository is set up, users can install via HACS:

1. **HACS** → **Integrations** → **⋮** → **Custom repositories**
2. Add: `https://github.com/YOUR_USERNAME/biocat`
3. Category: **Integration**
4. Install and restart Home Assistant

## Automatic Updates

The integration includes:
- ✅ GitHub workflows for validation
- ✅ Version management
- ✅ Release automation
- ✅ HACS compatibility

## Support

For questions about setting up your repository:
1. Check the [HACS documentation](https://hacs.xyz/docs/publish/integration)
2. Review existing HACS integrations for examples
3. Ask in the [Home Assistant Community](https://community.home-assistant.io/)