#!/bin/bash
#
# uninstall.sh - Uninstall HashiCorp Vault Credential Plugins from AAP 2.5
#
# This script removes the Vault credential plugins from AAP 2.5 (gateway architecture)
# and cleans up associated artifacts.
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="awx-vault-secrets-plugin"
PLUGIN_NAME="HashiCorp Vault Secrets Plugin"

# AAP 2.5 commands (use awx-python which automatically uses correct venv)
AAP_PYTHON="awx-python"
AAP_PIP="awx-python -m pip"
AUTOMATION_CONTROLLER_MANAGE="awx-manage"

# Service names for AAP 2.5
SERVICES=("automation-controller-server")

# Credential type names to look for
CREDENTIAL_TYPES=("HashiCorp Vault Authentication" "HashiCorp Vault AWS Secrets Engine Lookup")

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Uninstalling ${PLUGIN_NAME}${NC}"
    echo -e "${BLUE}  from Ansible Automation Platform 2.5${NC}"
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

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_prerequisites() {
    print_step "Checking prerequisites..."
    
    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (or with sudo)"
        exit 1
    fi
    
    # Check if AAP commands are available
    if ! command -v awx-python &> /dev/null; then
        print_error "awx-python command not found"
        print_error "This script is designed for AAP 2.5 with gateway architecture"
        exit 1
    fi
    
    if ! command -v awx-manage &> /dev/null; then
        print_error "awx-manage command not found"
        print_error "This script is designed for AAP 2.5 with gateway architecture"
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

check_package_installed() {
    print_step "Checking if package is installed..."
    
    if $AAP_PIP show "$PACKAGE_NAME" >/dev/null 2>&1; then
        print_success "Package is installed"
        return 0
    else
        print_warning "Package is not installed"
        return 1
    fi
}

warn_about_credentials() {
    print_step "Checking for existing credentials..."
    
    echo -e "${YELLOW}WARNING: This will remove the credential plugin but NOT delete existing credentials.${NC}"
    echo -e "${YELLOW}If you have created credentials using these types, they will become unusable.${NC}"
    echo
    echo -e "${BLUE}Before proceeding, you should:${NC}"
    echo "1. Remove any Job Templates using these credentials"
    echo "2. Delete any credentials of these types:"
    for cred_type in "${CREDENTIAL_TYPES[@]}"; do
        echo "   • $cred_type"
    done
    echo
    
    read -p "Do you want to continue with the uninstallation? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Uninstallation cancelled."
        exit 0
    fi
}

uninstall_package() {
    print_step "Uninstalling Python package..."
    
    if $AAP_PIP uninstall "$PACKAGE_NAME" -y --quiet; then
        print_success "Package uninstalled successfully"
    else
        print_error "Failed to uninstall package (it may not have been installed)"
    fi
}

clean_credential_types() {
    print_step "Cleaning up managed credential types..."
    
    # Re-run setup_managed_credential_types to remove orphaned types
    if $AUTOMATION_CONTROLLER_MANAGE setup_managed_credential_types; then
        print_success "Managed credential types updated"
    else
        print_warning "Failed to update managed credential types"
        echo "You may need to manually remove credential types from the web interface"
    fi
}

restart_services() {
    print_step "Restarting AAP services..."
    
    local failed_services=()
    
    for service in "${SERVICES[@]}"; do
        echo "  Restarting $service..."
        if systemctl restart "$service"; then
            print_success "  $service restarted"
        else
            print_error "  Failed to restart $service"
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        print_success "All services restarted successfully"
    else
        print_error "Failed to restart: ${failed_services[*]}"
        echo -e "${YELLOW}You may need to restart these services manually${NC}"
    fi
}

verify_removal() {
    print_step "Verifying removal..."
    
    # Check if plugins can still be imported
    if $AAP_PYTHON -c "import awx_vault_secrets_plugin" 2>/dev/null; then
        print_warning "Plugin package may still be importable (development installation?)"
    else
        print_success "Plugin package successfully removed"
    fi
    
    # Check if package is still listed
    if $AAP_PIP show "$PACKAGE_NAME" >/dev/null 2>&1; then
        print_warning "Package still appears to be installed"
    else
        print_success "Package no longer listed in pip"
    fi
}

clean_development_artifacts() {
    print_step "Cleaning development artifacts..."
    
    local cleaned=false
    
    # Look for common development artifacts
    local artifacts=(
        "awx_vault_secrets_plugin.egg-info"
        "build"
        "dist"
        "__pycache__"
        "*.pyc"
        ".pytest_cache"
    )
    
    for pattern in "${artifacts[@]}"; do
        if find /var/lib/awx -name "$pattern" -type d 2>/dev/null | grep -q .; then
            echo "  Removing $pattern directories..."
            find /var/lib/awx -name "$pattern" -type d -exec rm -rf {} + 2>/dev/null || true
            cleaned=true
        fi
        
        if find /var/lib/awx -name "$pattern" -type f 2>/dev/null | grep -q .; then
            echo "  Removing $pattern files..."
            find /var/lib/awx -name "$pattern" -type f -delete 2>/dev/null || true
            cleaned=true
        fi
    done
    
    if $cleaned; then
        print_success "Development artifacts cleaned"
    else
        print_success "No development artifacts found"
    fi
}

print_completion() {
    echo
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Uninstallation completed!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo
    echo -e "${BLUE}What was removed:${NC}"
    echo "• Python package: $PACKAGE_NAME"
    echo "• Entry points for credential plugins"
    echo "• Development artifacts (if any)"
    echo
    echo -e "${YELLOW}Manual cleanup required:${NC}"
    echo "1. Remove any remaining credentials of these types:"
    for cred_type in "${CREDENTIAL_TYPES[@]}"; do
        echo "   • $cred_type"
    done
    echo "2. Check Job Templates for references to removed credential types"
    echo "3. Review AAP logs for any related errors"
    echo
    echo -e "${BLUE}To verify complete removal:${NC}"
    echo "1. Log into the AAP web interface"
    echo "2. Go to Administration → Credential Types"
    echo "3. Confirm the Vault credential types are no longer listed"
    echo
}

# Main execution
main() {
    print_header
    check_prerequisites
    
    # Check if package is installed before proceeding
    if ! check_package_installed; then
        echo -e "${YELLOW}Package is not installed. Nothing to uninstall.${NC}"
        exit 0
    fi
    
    warn_about_credentials
    uninstall_package
    clean_credential_types
    clean_development_artifacts
    restart_services
    verify_removal
    print_completion
}

# Run main function
main "$@"
