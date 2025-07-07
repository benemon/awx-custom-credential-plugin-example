#!/bin/bash
#
# install.sh - Install HashiCorp Vault Credential Plugins for AAP 2.5
#
# This script installs the Vault credential plugins on AAP 2.5 (gateway architecture)
# and registers them with the automation controller.
#

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PACKAGE_NAME="awx-vault-secrets-plugin"
PLUGIN_NAME="HashiCorp Vault Secrets Plugin"

# AAP 2.5 commands (use awx-python which automatically uses correct venv)
AAP_PYTHON="awx-python"
AAP_PIP="awx-python -m pip"
AUTOMATION_CONTROLLER_MANAGE="awx-manage"

# Service names for AAP 2.5
SERVICES=("automation-controller-server")

print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}  Installing ${PLUGIN_NAME}${NC}"
    echo -e "${BLUE}  for Ansible Automation Platform 2.5${NC}"
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
    
    # Check if source directory exists
    if [[ ! -f "$SCRIPT_DIR/setup.py" ]]; then
        print_error "setup.py not found. Please run this script from the project root directory."
        exit 1
    fi
    
    print_success "Prerequisites check passed"
}

install_package() {
    print_step "Installing Python package..."
    
    # Install the package in development mode
    cd "$SCRIPT_DIR"
    
    if $AAP_PIP install -e . --quiet; then
        print_success "Package installed successfully"
    else
        print_error "Failed to install package"
        exit 1
    fi
}

register_plugins() {
    print_step "Registering credential plugins with automation controller..."
    
    # Register the plugins
    if $AUTOMATION_CONTROLLER_MANAGE setup_managed_credential_types; then
        print_success "Plugins registered successfully"
    else
        print_error "Failed to register plugins"
        exit 1
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

verify_installation() {
    print_step "Verifying installation..."
    
    # Check if plugins can be imported
    if $AAP_PYTHON -c "
import awx_vault_secrets_plugin
from awx_vault_secrets_plugin import vault_auth_plugin, vault_aws_lookup_plugin
print('✓ Plugins imported successfully')
print(f'  - {vault_auth_plugin.name}')
print(f'  - {vault_aws_lookup_plugin.name}')
" 2>/dev/null; then
        print_success "Plugin verification passed"
    else
        print_error "Plugin verification failed"
        exit 1
    fi
}

print_completion() {
    echo
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  Installation completed successfully!${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Log into the AAP web interface"
    echo "2. Navigate to Administration → Credential Types"
    echo "3. Look for these new credential types:"
    echo "   • HashiCorp Vault Authentication"
    echo "   • HashiCorp Vault AWS Secrets Engine Lookup"
    echo
    echo -e "${BLUE}To create credentials:${NC}"
    echo "1. Go to Resources → Credentials → Add"
    echo "2. Select the appropriate Vault credential type"
    echo "3. Configure your Vault connection details"
    echo
    echo -e "${YELLOW}Need help? Check the README.md for configuration examples.${NC}"
    echo
}

# Main execution
main() {
    print_header
    check_prerequisites
    install_package
    register_plugins
    restart_services
    verify_installation
    print_completion
}

# Run main function
main "$@"
