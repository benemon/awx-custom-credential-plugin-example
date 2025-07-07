"""
HashiCorp Vault Credential Plugins for AWX/AAP.

This package provides comprehensive credential plugins for HashiCorp Vault integration
with Ansible Automation Platform (AAP) and AWX.

Available Plugins:
- vault_auth_plugin: Authentication credential for Vault connection
- vault_aws_lookup_plugin: AWS secrets engine credential lookup
"""

from .vault_auth import vault_auth_plugin
from .vault_aws_lookup import vault_aws_lookup_plugin

__all__ = ['vault_auth_plugin', 'vault_aws_lookup_plugin']
