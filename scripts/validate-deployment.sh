#!/bin/bash
# Validation script for production Docker deployment
# Run this before deploying to production

set -e

echo "==================================="
echo "RIMS Production Deployment Validator"
echo "==================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

errors=0
warnings=0

# Check if running in project root
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}ERROR: docker-compose.yml not found. Run this script from project root.${NC}"
    exit 1
fi

echo "✓ Running from project root"
echo ""

# Check required files
echo "Checking required files..."
required_files=(
    "docker-compose.yml"
    "backend/Dockerfile"
    "backend/requirements.txt"
    "frontend/Dockerfile"
    "frontend/nginx.prod.conf"
    "scripts/entrypoint.sh"
    ".env.prod.example"
    "README_PROD.md"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "  ${GREEN}✓${NC} $file"
    else
        echo -e "  ${RED}✗${NC} $file - MISSING"
        ((errors++))
    fi
done
echo ""

# Check .env.prod exists
echo "Checking environment configuration..."
if [ -f ".env.prod" ]; then
    echo -e "  ${GREEN}✓${NC} .env.prod exists"
    
    # Check for placeholder values
    if grep -q "CHANGE_ME" .env.prod; then
        echo -e "  ${YELLOW}⚠${NC} .env.prod contains placeholder values (CHANGE_ME)"
        ((warnings++))
    fi
    
    # Check for required variables
    required_vars=("DJANGO_SECRET_KEY" "DB_PASSWORD" "DJANGO_ALLOWED_HOSTS")
    for var in "${required_vars[@]}"; do
        if grep -q "^${var}=" .env.prod; then
            echo -e "  ${GREEN}✓${NC} $var is set"
        else
            echo -e "  ${RED}✗${NC} $var is missing"
            ((errors++))
        fi
    done
else
    echo -e "  ${YELLOW}⚠${NC} .env.prod not found (copy from .env.prod.example)"
    ((warnings++))
fi
echo ""

# Check Docker
echo "Checking Docker installation..."
if command -v docker &> /dev/null; then
    docker_version=$(docker --version)
    echo -e "  ${GREEN}✓${NC} Docker installed: $docker_version"
else
    echo -e "  ${RED}✗${NC} Docker not found"
    ((errors++))
fi

# Check Docker Compose (v2 preferred, v1 supported with warning)
if docker compose version &> /dev/null; then
    compose_version=$(docker compose version)
    echo -e "  ${GREEN}✓${NC} Docker Compose v2 installed (docker compose): $compose_version"
elif command -v docker-compose &> /dev/null; then
    compose_version=$(docker-compose version)
    echo -e "  ${YELLOW}⚠${NC} Docker Compose v1 installed (docker-compose): $compose_version"
    echo -e "     ${YELLOW}Deployment is tested with Docker Compose v2 ('docker compose'). Consider upgrading.${NC}"
    ((warnings++))
else
    echo -e "  ${RED}✗${NC} Docker Compose not found (neither 'docker compose' nor 'docker-compose' is available)"
    ((errors++))
fi
echo ""

# Check entrypoint script is executable
echo "Checking script permissions..."
if [ -x "scripts/entrypoint.sh" ]; then
    echo -e "  ${GREEN}✓${NC} scripts/entrypoint.sh is executable"
else
    echo -e "  ${YELLOW}⚠${NC} scripts/entrypoint.sh is not executable (will be handled by Docker)"
    ((warnings++))
fi
echo ""

# Check for common issues in docker-compose.yml
echo "Validating docker-compose.yml..."
if grep -q "version:" docker-compose.yml; then
    echo -e "  ${GREEN}✓${NC} docker-compose.yml syntax appears valid"
else
    echo -e "  ${YELLOW}⚠${NC} docker-compose.yml may have syntax issues"
    ((warnings++))
fi

if grep -q "127.0.0.1:8015:8000" docker-compose.yml; then
    echo -e "  ${GREEN}✓${NC} Backend bound to localhost only (secure)"
else
    echo -e "  ${YELLOW}⚠${NC} Backend port binding not found or insecure"
    ((warnings++))
fi

if grep -q "127.0.0.1:8081:80" docker-compose.yml; then
    echo -e "  ${GREEN}✓${NC} Frontend bound to localhost only (secure)"
else
    echo -e "  ${YELLOW}⚠${NC} Frontend port binding not found or insecure"
    ((warnings++))
fi
echo ""

# Summary
echo "==================================="
echo "Validation Summary"
echo "==================================="
if [ $errors -eq 0 ] && [ $warnings -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Ready for deployment.${NC}"
    exit 0
elif [ $errors -eq 0 ]; then
    echo -e "${YELLOW}⚠ $warnings warning(s) found. Review before deployment.${NC}"
    exit 0
else
    echo -e "${RED}✗ $errors error(s) and $warnings warning(s) found. Fix errors before deployment.${NC}"
    exit 1
fi
