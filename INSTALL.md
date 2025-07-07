# Installation Scripts for AAP 2.5

This directory contains automated installation and uninstallation scripts for the HashiCorp Vault secrets plugin on Ansible Automation Platform 2.5.

## Quick Start

### Install the plugins:
```bash
sudo ./install.sh
```

### Uninstall the plugins:
```bash
sudo ./uninstall.sh
```

### Test the scripts (development):
```bash
./test_scripts.sh
```

## Scripts Overview

### `install.sh`
Automated installation script for AAP 2.5 with gateway architecture.

**What it does:**
- ✅ Validates AAP 2.5 environment and prerequisites
- ✅ Installs the Python package in AAP's virtual environment
- ✅ Registers credential plugins with `awx-manage setup_managed_credential_types`
- ✅ Restarts AAP services (automation-controller-task, automation-controller-web, receptor)
- ✅ Verifies successful installation

**Requirements:**
- Must be run as root (or with `sudo`)
- AAP 2.5 installed with gateway architecture
- Available commands: `awx-python` and `awx-manage`

### `uninstall.sh`
Automated uninstallation script with safety checks.

**What it does:**
- ⚠️  Warns about existing credentials that will become unusable
- ✅ Uninstalls the Python package
- ✅ Cleans up managed credential types
- ✅ Removes development artifacts
- ✅ Restarts AAP services
- ✅ Verifies complete removal

**Safety features:**
- Interactive confirmation before proceeding
- Warns about credentials that will be affected
- Provides manual cleanup guidance

### `test_scripts.sh`
Development test script to validate script functionality.

**What it tests:**
- Script syntax validation
- File permissions
- Error handling
- Package structure compatibility

## Usage Examples

### Standard Installation
```bash
# 1. Copy the project to your AAP server
scp -r vault-plugins/ root@aap-server:/tmp/

# 2. SSH to AAP server and install
ssh root@aap-server
cd /tmp/vault-plugins/
./install.sh
```

### Development/Testing Installation
```bash
# Test locally first
./test_scripts.sh

# Install on AAP
sudo ./install.sh

# Check the web interface for new credential types
# Navigate to: Administration → Credential Types
```

### Safe Uninstallation
```bash
# The script will warn you about existing credentials
sudo ./uninstall.sh

# Follow the prompts and cleanup guidance
```

## Troubleshooting

### Common Issues

**"This script must be run as root"**
- Solution: Use `sudo ./install.sh` or run as root

**"awx-python command not found"**
- Check if AAP 2.5 is properly installed
- Verify the gateway architecture is in use
- Ensure AAP commands are in PATH

**"Failed to restart services"**
- Check service status: `systemctl status automation-controller-task`
- View logs: `journalctl -u automation-controller-task -f`
- Manual restart: `systemctl restart automation-controller-task automation-controller-web`

**Plugin not appearing in web interface**
- Wait a few minutes after installation
- Check AWX logs: `tail -f /var/log/tower/tower.log`
- Try hard refresh in browser (Ctrl+F5)

### Manual Verification

**Check if package is installed:**
```bash
awx-python -m pip show awx-vault-secrets-plugin
```

**Test plugin import:**
```bash
awx-python -c "
from awx_vault_secrets_plugin import vault_auth_plugin, vault_aws_lookup_plugin
print('✓ Plugins loaded successfully')
"
```

**List registered credential types:**
```bash
awx-manage shell -c "
from awx.main.models import CredentialType
for ct in CredentialType.objects.filter(managed=True):
    if 'vault' in ct.name.lower():
        print(f'{ct.name} (managed={ct.managed})')
"
```

## File Structure After Installation

```
# Commands available on AAP 2.5:
awx-python                          # Python in AAP venv
awx-manage                          # Django management command
awx-python -m pip                   # Package installation

# Installed package location:
/var/lib/awx/venv/awx/lib/python3.x/site-packages/awx_vault_secrets_plugin/
```

## Security Considerations

- Scripts require root access to modify AAP installation
- Test in non-production environment first
- Back up your AAP configuration before installation
- Review script contents before execution
- Uninstallation affects all users' credentials of these types

## Support

If you encounter issues:

1. Run `./test_scripts.sh` to verify basic functionality
2. Check AAP logs for detailed error messages
3. Verify AAP 2.5 installation and gateway architecture
4. Ensure all AAP services are running properly

For additional help, refer to the main [README.md](README.md) for configuration examples and troubleshooting guides.
