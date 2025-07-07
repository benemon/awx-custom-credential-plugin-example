#!/bin/bash
#
# test_scripts.sh - Test the install/uninstall scripts in a safe environment
#
# This script tests the install and uninstall scripts without requiring
# actual AAP installation (for development/testing purposes).
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Testing Install/Uninstall Scripts${NC}"
    echo -e "${BLUE}  for HashiCorp Vault Secrets Plugin${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
}

print_step() {
    echo -e "${YELLOW}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

test_script_syntax() {
    print_step "Testing script syntax..."
    
    # Test install.sh syntax
    if bash -n install.sh; then
        print_success "install.sh syntax is valid"
    else
        print_error "install.sh has syntax errors"
        return 1
    fi
    
    # Test uninstall.sh syntax
    if bash -n uninstall.sh; then
        print_success "uninstall.sh syntax is valid"
    else
        print_error "uninstall.sh has syntax errors"
        return 1
    fi
}

test_script_permissions() {
    print_step "Testing script permissions..."
    
    if [[ -x install.sh ]]; then
        print_success "install.sh is executable"
    else
        print_error "install.sh is not executable"
        return 1
    fi
    
    if [[ -x uninstall.sh ]]; then
        print_success "uninstall.sh is executable"
    else
        print_error "uninstall.sh is not executable"
        return 1
    fi
}

test_help_output() {
    print_step "Testing script help/info output..."
    
    # The scripts should show helpful error messages when prerequisites aren't met
    echo "  Testing install.sh (should fail gracefully)..."
    if ./install.sh 2>&1 | grep -q "must be run as root"; then
        print_success "  install.sh shows appropriate error for non-root execution"
    else
        print_error "  install.sh doesn't show expected error message"
    fi
    
    echo "  Testing uninstall.sh (should fail gracefully)..."
    if ./uninstall.sh 2>&1 | grep -q "must be run as root"; then
        print_success "  uninstall.sh shows appropriate error for non-root execution"
    else
        print_error "  uninstall.sh doesn't show expected error message"
    fi
}

test_package_structure() {
    print_step "Testing package structure compatibility..."
    
    # Check if the package structure is compatible with the scripts
    if [[ -f setup.py ]]; then
        print_success "setup.py found"
    else
        print_error "setup.py not found"
        return 1
    fi
    
    if [[ -d awx_vault_secrets_plugin ]]; then
        print_success "Plugin package directory found"
    else
        print_error "Plugin package directory not found"
        return 1
    fi
    
    # Test that the package can be imported
    if python -c "import awx_vault_secrets_plugin" 2>/dev/null; then
        print_success "Package can be imported"
    else
        print_error "Package cannot be imported"
        return 1
    fi
}

print_usage_info() {
    echo
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Script Testing Complete${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo
    echo -e "${YELLOW}Usage on AAP 2.5 systems:${NC}"
    echo
    echo -e "${GREEN}To install:${NC}"
    echo "  sudo ./install.sh"
    echo
    echo -e "${GREEN}To uninstall:${NC}"
    echo "  sudo ./uninstall.sh"
    echo
    echo -e "${BLUE}Prerequisites for AAP systems:${NC}"
    echo "• Must be run as root (or with sudo)"
    echo "• AAP 2.5 must be installed with gateway architecture"
    echo "• Required commands:"
    echo "  - awx-python"
    echo "  - awx-manage"
    echo
    echo -e "${YELLOW}What the scripts do:${NC}"
    echo
    echo -e "${GREEN}install.sh:${NC}"
    echo "• Installs the Python package in AAP's virtual environment"
    echo "• Registers credential plugins with automation controller"
    echo "• Restarts AAP services"
    echo "• Verifies installation"
    echo
    echo -e "${GREEN}uninstall.sh:${NC}"
    echo "• Warns about existing credentials that will become unusable"
    echo "• Uninstalls the Python package"
    echo "• Cleans up managed credential types"
    echo "• Removes development artifacts"
    echo "• Restarts AAP services"
    echo
}

# Main execution
main() {
    print_header
    
    local all_passed=true
    
    test_script_syntax || all_passed=false
    test_script_permissions || all_passed=false
    test_help_output || all_passed=false
    test_package_structure || all_passed=false
    
    if $all_passed; then
        print_success "All tests passed!"
        print_usage_info
        exit 0
    else
        print_error "Some tests failed!"
        exit 1
    fi
}

# Run main function
main "$@"
