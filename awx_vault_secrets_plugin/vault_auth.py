"""
HashiCorp Vault Authentication Credential Plugin for AWX/AAP.

This plugin provides authentication credentials for HashiCorp Vault,
supporting token, AppRole, and JWT authentication methods.
"""

import collections
from .common.vault_client import VaultClient, VaultAuthenticationError

CredentialPlugin = collections.namedtuple('CredentialPlugin', ['name', 'inputs', 'backend'])


def vault_auth_backend(**kwargs):
    """
    Vault authentication backend function.
    
    This function validates Vault authentication credentials by attempting
    to authenticate with the provided parameters.
    
    Args:
        **kwargs: Authentication parameters from the credential inputs
        
    Returns:
        dict: Success message indicating valid authentication
        
    Raises:
        Exception: If authentication fails
    """
    # Extract authentication parameters
    url = kwargs.get('url')
    if not url:
        raise ValueError("Vault URL is required")
    
    # SSL/TLS settings
    verify_ssl = kwargs.get('verify_ssl', True)
    ca_cert = kwargs.get('ca_cert')
    namespace = kwargs.get('namespace')
    
    # Create Vault client
    client = VaultClient(
        url=url,
        verify_ssl=verify_ssl,
        ca_cert=ca_cert,
        namespace=namespace
    )
    
    # Determine authentication method based on provided parameters
    if kwargs.get('token'):
        auth_method = 'token'
        auth_params = {'token': kwargs['token']}
    elif kwargs.get('role_id') and kwargs.get('secret_id'):
        auth_method = 'approle'
        auth_params = {
            'role_id': kwargs['role_id'],
            'secret_id': kwargs['secret_id'],
            'auth_path': kwargs.get('auth_path', 'approle')
        }
    elif kwargs.get('jwt_token') and kwargs.get('jwt_role'):
        auth_method = 'jwt'
        auth_params = {
            'jwt_token': kwargs['jwt_token'],
            'role': kwargs['jwt_role'],
            'auth_path': kwargs.get('jwt_auth_path', 'jwt')
        }
    else:
        raise ValueError("No valid authentication method provided. Please provide either: token, role_id+secret_id, or jwt_token+jwt_role")
    
    try:
        # Attempt authentication
        token = client.authenticate(auth_method, **auth_params)
        
        # Verify token by making a simple API call
        response = client.make_request('GET', 'auth/token/lookup-self', token)
        token_info = response.json()
        
        # Return success information
        return {
            'status': 'authenticated',
            'auth_method': auth_method,
            'token_ttl': token_info.get('data', {}).get('ttl', 'unknown'),
            'policies': token_info.get('data', {}).get('policies', [])
        }
        
    except VaultAuthenticationError as e:
        raise ValueError(f"Vault authentication failed: {e}")
    except Exception as e:
        raise ValueError(f"Vault connection failed: {e}")


vault_auth_plugin = CredentialPlugin(
    'HashiCorp Vault Authentication',
    inputs={
        'fields': [
            {
                'id': 'url',
                'label': 'Vault URL',
                'type': 'string',
                'format': 'url',
                'help_text': 'The URL to the HashiCorp Vault server (e.g., https://vault.example.com:8200)'
            },
            {
                'id': 'namespace',
                'label': 'Namespace',
                'type': 'string',
                'help_text': 'Vault Enterprise namespace (optional)'
            },
            {
                'id': 'verify_ssl',
                'label': 'Verify SSL',
                'type': 'boolean',
                'default': True,
                'help_text': 'Verify SSL certificates when connecting to Vault'
            },
            {
                'id': 'ca_cert',
                'label': 'CA Certificate',
                'type': 'string',
                'multiline': True,
                'help_text': 'CA certificate to verify the Vault server SSL certificate'
            },
            # Token Authentication
            {
                'id': 'token',
                'label': 'Vault Token',
                'type': 'string',
                'secret': True,
                'help_text': 'Vault authentication token (for token-based auth)'
            },
            # AppRole Authentication
            {
                'id': 'role_id',
                'label': 'AppRole Role ID',
                'type': 'string',
                'help_text': 'AppRole Role ID (for AppRole authentication)'
            },
            {
                'id': 'secret_id',
                'label': 'AppRole Secret ID',
                'type': 'string',
                'secret': True,
                'help_text': 'AppRole Secret ID (for AppRole authentication)'
            },
            {
                'id': 'auth_path',
                'label': 'AppRole Auth Path',
                'type': 'string',
                'default': 'approle',
                'help_text': 'Path where AppRole auth method is mounted (default: approle)'
            },
            # JWT Authentication
            {
                'id': 'jwt_token',
                'label': 'JWT Token',
                'type': 'string',
                'secret': True,
                'help_text': 'JWT token (for JWT authentication)'
            },
            {
                'id': 'jwt_role',
                'label': 'JWT Role',
                'type': 'string',
                'help_text': 'JWT role name (for JWT authentication)'
            },
            {
                'id': 'jwt_auth_path',
                'label': 'JWT Auth Path',
                'type': 'string',
                'default': 'jwt',
                'help_text': 'Path where JWT auth method is mounted (default: jwt)'
            }
        ],
        'required': ['url']
    },
    backend=vault_auth_backend
)
