#!/bin/bash

# Release script for WaterCryst BIOCAT Home Assistant Integration
# This script prepares a release for HACS

set -e

# Check if version parameter is provided
if [ $# -eq 0 ]; then
    echo "❌ Error: Version number required"
    echo "Usage: $0 <version>"
    echo "Example: $0 1.0.1"
    exit 1
fi

VERSION="$1"

echo "🚀 Preparing release $VERSION for WaterCryst BIOCAT integration"

# Validate version format (basic check)
if ! [[ $VERSION =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    echo "❌ Error: Invalid version format. Use semantic versioning (e.g., 1.0.1)"
    exit 1
fi

# Update VERSION file
echo "$VERSION" > VERSION
echo "✅ Updated VERSION file"

# Update manifest.json
sed -i "s/\"version\": \".*\"/\"version\": \"$VERSION\"/" custom_components/watercryst/manifest.json
echo "✅ Updated manifest.json version"

# Create release directory and zip file for HACS
RELEASE_DIR="release"
ZIP_FILE="watercryst-$VERSION.zip"

rm -rf "$RELEASE_DIR"
mkdir -p "$RELEASE_DIR"

# Copy integration files
cp -r custom_components "$RELEASE_DIR/"
echo "✅ Copied integration files"

# Create zip file
cd "$RELEASE_DIR"
zip -r "../$ZIP_FILE" custom_components/
cd ..

echo "✅ Created release package: $ZIP_FILE"

# Clean up
rm -rf "$RELEASE_DIR"

echo ""
echo "📦 Release $VERSION is ready!"
echo ""
echo "Next steps:"
echo "1. Commit the version changes:"
echo "   git add VERSION custom_components/watercryst/manifest.json"
echo "   git commit -m 'Release $VERSION'"
echo "   git tag v$VERSION"
echo "   git push origin main --tags"
echo ""
echo "2. Create a GitHub release:"
echo "   - Go to GitHub → Releases → New Release"
echo "   - Tag: v$VERSION"
echo "   - Title: v$VERSION"
echo "   - Upload the zip file: $ZIP_FILE"
echo ""
echo "3. HACS will automatically detect the new release!"