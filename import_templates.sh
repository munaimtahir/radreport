#!/bin/bash
#
# Import USG Templates Script
# 
# This script helps you import USG templates and link them to services.
# Place your template JSON files in /tmp/ and run this script.
#
# Usage:
#   ./import_templates.sh
#

set -e

echo "=========================================="
echo "USG Template Import Helper"
echo "=========================================="
echo ""

cd "$(dirname "$0")"
source .venv/bin/activate
cd backend

# Check if management command exists
if [ ! -f "apps/templates/management/commands/import_usg_template.py" ]; then
    echo "❌ Error: import_usg_template command not found!"
    echo "Make sure you're running from the project root."
    exit 1
fi

echo "📁 Looking for template files in /tmp/*.json..."
echo ""

TEMPLATES_FOUND=0
TEMPLATES_IMPORTED=0
TEMPLATES_FAILED=0

for template_file in /tmp/usg_*.json /tmp/USG_*.json; do
    if [ -f "$template_file" ]; then
        TEMPLATES_FOUND=$((TEMPLATES_FOUND + 1))
        
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📄 Found: $template_file"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        
        # Extract template code from JSON
        TEMPLATE_CODE=$(cat "$template_file" | grep -o '"code"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:.*"\(.*\)".*/\1/')
        
        if [ -z "$TEMPLATE_CODE" ]; then
            echo "⚠️  Warning: Could not extract template code from $template_file"
            TEMPLATES_FAILED=$((TEMPLATES_FAILED + 1))
            continue
        fi
        
        echo "Template code: $TEMPLATE_CODE"
        echo ""
        
        # Try to guess service code from template code
        # USG_ABDOMEN_BASIC → USG_ABDOMEN
        SERVICE_CODE=$(echo "$TEMPLATE_CODE" | sed 's/_BASIC$//' | sed 's/_ADVANCED$//')
        
        echo "Attempting import..."
        if python manage.py import_usg_template "$template_file" --link-service="$SERVICE_CODE"; then
            echo "✅ Success!"
            TEMPLATES_IMPORTED=$((TEMPLATES_IMPORTED + 1))
        else
            echo "❌ Failed!"
            TEMPLATES_FAILED=$((TEMPLATES_FAILED + 1))
        fi
        
        echo ""
    fi
done

if [ $TEMPLATES_FOUND -eq 0 ]; then
    echo "ℹ️  No template files found in /tmp/"
    echo ""
    echo "To use this script:"
    echo "  1. Save your JSON templates to /tmp/ with names like:"
    echo "     /tmp/usg_abdomen.json"
    echo "     /tmp/usg_kub.json"
    echo "     etc."
    echo ""
    echo "  2. Run this script again: ./import_templates.sh"
    echo ""
    echo "Or import manually:"
    echo "  python manage.py import_usg_template /path/to/template.json --link-service=USG_XXX"
    echo ""
else
    echo "=========================================="
    echo "Import Summary"
    echo "=========================================="
    echo "Templates found: $TEMPLATES_FOUND"
    echo "Successfully imported: $TEMPLATES_IMPORTED"
    echo "Failed: $TEMPLATES_FAILED"
    echo "=========================================="
    echo ""
    
    if [ $TEMPLATES_IMPORTED -gt 0 ]; then
        echo "✅ Templates imported successfully!"
        echo ""
        echo "Next steps:"
        echo "  1. Verify linkage:"
        echo "     python manage.py link_usg_services --dry-run"
        echo ""
        echo "  2. Link any unmatched services:"
        echo "     python manage.py link_usg_services"
        echo ""
        echo "  3. Test in browser:"
        echo "     https://rims.alshifalab.pk"
        echo ""
    fi
fi
