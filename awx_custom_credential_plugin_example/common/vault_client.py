"""
HashiCorp Vault authentication utilities for AWX credential plugins.

This module provides common authentication methods for Vault credential plugins,
supporting token-based, AppRole, and JWT authentication methods.
"""

import time
from urllib.parse import urljoin
import requests


class VaultAuthenticationError(Exception):
    """Raised when Vault authentication fails."""
    pass


class VaultClient:
    """A simple Vault HTTP client with authentication support."""
    
    def __init__(self, url, verify_ssl=True, ca_cert=None, namespace=None):
        self.url = url.rstrip('/')
        self.verify_ssl = verify_ssl
        self.ca_cert = ca_cert
        self.namespace = namespace
        self.session = requests.Session()
        self.session.mount(url, requests.adapters.HTTPAdapter(max_retries=3))
        
        # Set up SSL verification
        if ca_cert:
            # In a real implementation, you'd write ca_cert to a temp file
            # and set verify to that path
            self.session.verify = verify_ssl
        else:
            self.session.verify = verify_ssl
    
    def authenticate(self, auth_method='token', **auth_params):
        """
        Authenticate with Vault and return a token.
        
        Args:
            auth_method: Authentication method ('token', 'approle', 'jwt')
            **auth_params: Authentication parameters specific to the method
            
        Returns:
            str: Vault authentication token
            
        Raises:
            VaultAuthenticationError: If authentication fails
        """
        if auth_method == 'token':
            return self._token_auth(**auth_params)
        elif auth_method == 'approle':
            return self._approle_auth(**auth_params)
        elif auth_method == 'jwt':
            return self._jwt_auth(**auth_params)
        else:
            raise VaultAuthenticationError(f"Unsupported auth method: {auth_method}")
    
    def _token_auth(self, token, **kwargs):
        """Direct token authentication."""
        if not token:
            raise VaultAuthenticationError("Token is required for token authentication")
        return token
    
    def _approle_auth(self, role_id, secret_id, auth_path='approle', **kwargs):
        """AppRole authentication."""
        if not role_id or not secret_id:
            raise VaultAuthenticationError("role_id and secret_id are required for AppRole authentication")
        
        url = urljoin(self.url, f'v1/auth/{auth_path}/login')
        data = {
            'role_id': role_id,
            'secret_id': secret_id
        }
        
        headers = {}
        if self.namespace:
            headers['X-Vault-Namespace'] = self.namespace
            
        try:
            response = self.session.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['auth']['client_token']
        except (requests.RequestException, KeyError) as e:
            raise VaultAuthenticationError(f"AppRole authentication failed: {e}")
    
    def _jwt_auth(self, jwt_token, role, auth_path='jwt', **kwargs):
        """JWT authentication."""
        if not jwt_token or not role:
            raise VaultAuthenticationError("jwt_token and role are required for JWT authentication")
        
        url = urljoin(self.url, f'v1/auth/{auth_path}/login')
        data = {
            'jwt': jwt_token,
            'role': role
        }
        
        headers = {}
        if self.namespace:
            headers['X-Vault-Namespace'] = self.namespace
            
        try:
            response = self.session.post(url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            result = response.json()
            return result['auth']['client_token']
        except (requests.RequestException, KeyError) as e:
            raise VaultAuthenticationError(f"JWT authentication failed: {e}")
    
    def make_request(self, method, path, token, namespace_override=None, **kwargs):
        """
        Make an authenticated request to Vault.
        
        Args:
            method: HTTP method ('GET', 'POST', etc.)
            path: Vault API path (without /v1/ prefix)
            token: Authentication token
            namespace_override: Optional namespace override
            **kwargs: Additional requests parameters
            
        Returns:
            requests.Response: The response object
        """
        url = urljoin(self.url, f'v1/{path}')
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-Vault-Token': token,  # Compatibility header
        }
        
        # Use namespace override if provided, otherwise use client default
        namespace = namespace_override or self.namespace
        if namespace:
            headers['X-Vault-Namespace'] = namespace
            
        kwargs.setdefault('timeout', 30)
        kwargs.setdefault('allow_redirects', False)
        
        # Handle retries for consistency issues (Vault Enterprise)
        max_retries = 5
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, headers=headers, **kwargs)
                
                # Handle Vault Enterprise consistency issues
                if response.status_code == 412:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(1)
        
        raise VaultAuthenticationError("Max retries exceeded")


def get_auth_headers(namespace=None):
    """Get standard Vault authentication headers."""
    headers = {}
    if namespace:
        headers['X-Vault-Namespace'] = namespace
    return headers
