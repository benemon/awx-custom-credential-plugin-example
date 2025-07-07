"""
HashiCorp Vault AWS Secrets Engine Lookup Plugin for AWX/AAP.

This plugin retrieves dynamic AWS credentials from HashiCorp Vault's AWS secrets engine.
It supports both IAM user credentials and STS assume role tokens.

Since AWX is a one-shot environment, this plugin does not handle credential lifecycle
management such as TTL tracking or renewal. The responsibility for credential lifecycle
is placed on the user and their Vault configuration.
"""

import collections
from .common.vault_client import VaultClient, VaultAuthenticationError

CredentialPlugin = collections.namedtuple('CredentialPlugin', ['name', 'inputs', 'backend'])


def vault_aws_backend(**kwargs):
    """
    Vault AWS secrets engine backend function.
    
    This function retrieves dynamic AWS credentials from Vault's AWS secrets engine.
    
    Args:
        **kwargs: Parameters from both auth and lookup credentials
        
    Returns:
        dict: AWS credentials (access_key_id, secret_access_key, etc.)
        
    Raises:
        Exception: If credential retrieval fails
    """
    # Extract auth parameters (these come from the linked auth credential)
    auth_url = kwargs.get('url')
    auth_token = kwargs.get('token')
    auth_namespace = kwargs.get('namespace')
    auth_verify_ssl = kwargs.get('verify_ssl', True)
    auth_ca_cert = kwargs.get('ca_cert')
    
    # Extract AppRole auth if token not provided
    if not auth_token:
        if kwargs.get('role_id') and kwargs.get('secret_id'):
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
            raise ValueError("Authentication credentials are required")
    
    # Extract lookup parameters (these come from the lookup credential metadata)
    mount_path = kwargs.get('mount_path', 'aws')
    role_name = kwargs.get('role_name')
    credential_type = kwargs.get('credential_type', 'creds')  # 'creds' or 'sts'
    lookup_namespace = kwargs.get('namespace')  # Namespace from lookup credential
    
    if not role_name:
        raise ValueError("AWS role name is required")
    
    if not auth_url:
        raise ValueError("Vault URL is required from auth credential")
    
    # Create Vault client
    client = VaultClient(
        url=auth_url,
        verify_ssl=auth_verify_ssl,
        ca_cert=auth_ca_cert,
        namespace=auth_namespace
    )
    
    try:
        # Authenticate if we don't have a token
        if not auth_token:
            auth_token = client.authenticate(auth_method, **auth_params)
        
        # Build the path based on credential type
        if credential_type == 'sts':
            path = f"{mount_path}/sts/{role_name}"
        else:
            path = f"{mount_path}/creds/{role_name}"
        
        # Make the request to get AWS credentials
        response = client.make_request(
            'GET', 
            path, 
            auth_token,
            namespace_override=lookup_namespace
        )
        
        result = response.json()
        data = result.get('data', {})
        
        if not data:
            raise ValueError("No credential data returned from Vault")
        
        # Return AWS credentials in a standard format
        aws_creds = {}
        
        # Standard AWS credential fields
        if 'access_key' in data:
            aws_creds['access_key_id'] = data['access_key']
        if 'secret_key' in data:
            aws_creds['secret_access_key'] = data['secret_key']
        if 'security_token' in data:
            aws_creds['session_token'] = data['security_token']
        
        # STS-specific fields
        if 'arn' in data:
            aws_creds['arn'] = data['arn']
        
        # Add credential type information for debugging/reference
        aws_creds['credential_type'] = credential_type
        aws_creds['vault_role'] = role_name
        
        return aws_creds
        
    except VaultAuthenticationError as e:
        raise ValueError(f"Vault authentication failed: {e}")
    except Exception as e:
        raise ValueError(f"Failed to retrieve AWS credentials: {e}")


vault_aws_lookup_plugin = CredentialPlugin(
    'HashiCorp Vault AWS Secrets Engine Lookup',
    inputs={
        'fields': [
            # These fields would typically be populated by AAP when linking credentials
            # But we include them for completeness and direct usage scenarios
        ],
        'metadata': [
            {
                'id': 'mount_path',
                'label': 'AWS Mount Path',
                'type': 'string',
                'default': 'aws',
                'help_text': 'Path where the AWS secrets engine is mounted in Vault'
            },
            {
                'id': 'role_name',
                'label': 'AWS Role Name',
                'type': 'string',
                'help_text': 'Name of the AWS role configured in Vault to generate credentials for'
            },
            {
                'id': 'credential_type',
                'label': 'Credential Type',
                'type': 'string',
                'choices': ['creds', 'sts'],
                'default': 'creds',
                'help_text': 'Type of AWS credentials to generate (creds=IAM user, sts=assume role)'
            },
            {
                'id': 'namespace',
                'label': 'Namespace',
                'type': 'string',
                'help_text': 'Vault Enterprise namespace for this lookup (optional)'
            }
        ],
        'required': ['role_name']
    },
    backend=vault_aws_backend
)
