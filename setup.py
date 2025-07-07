#!/usr/bin/env python

from setuptools import setup

requirements = [
    "requests>=2.25.0",
]

setup(
    name='awx-vault-secrets-plugin',
    version='0.1.0',
    author='AWX Vault Secrets Plugin',
    author_email='',
    description='HashiCorp Vault secrets plugin for AWX/AAP',
    long_description='A comprehensive credential plugin for HashiCorp Vault secrets integration with Ansible Automation Platform',
    license='Apache License 2.0',
    keywords='ansible vault hashicorp awx aap',
    url='http://github.com/ansible/awx-custom-credential-plugin-example',
    packages=['awx_vault_secrets_plugin'],
    include_package_data=True,
    zip_safe=False,
    setup_requires=[],
    install_requires=requirements,
    entry_points = {
        'awx.credential_plugins': [
            'vault_auth = awx_vault_secrets_plugin:vault_auth_plugin',
            'vault_aws_lookup = awx_vault_secrets_plugin:vault_aws_lookup_plugin',
        ]
    }
)
