# HashiCorp Vault Secrets Plugin for AWX/AAP

This repository contains a comprehensive credential plugin for integrating HashiCorp Vault with Ansible Automation Platform (AAP) and AWX. The plugin is designed to support retrieval of dynamic secrets from various Vault secret engines with a focus on simplicity and AWX's one-shot execution model.

## 🎯 Design Philosophy

- **One-Shot Execution**: Designed for AWX's stateless execution environment - no credential lifecycle management
- **User Responsibility**: Credential TTL and renewal management is handled by Vault configuration, not the plugin
- **Simplified UX**: Clean separation between authentication and lookup with intuitive field naming
- **Extensible Architecture**: Modular design allows easy addition of new secret engines

## 📦 Available Plugins

### 1. Vault Authentication Plugin (`vault_auth_plugin`)
Provides authentication credentials and connection details for HashiCorp Vault.

**Supported Authentication Methods:**
- **Token Authentication**: Direct Vault token
- **AppRole Authentication**: Role ID + Secret ID  
- **JWT Authentication**: JWT token + role name

**Configuration Fields:**
- `url` (required): Vault server URL
- `namespace` (optional): Vault Enterprise namespace for authentication
- `verify_ssl` (boolean): SSL certificate verification (default: true)
- `ca_cert` (optional): CA certificate for SSL verification
- `token` (secret): Vault authentication token
- `role_id`: AppRole Role ID
- `secret_id` (secret): AppRole Secret ID
- `auth_path`: AppRole auth mount path (default: "approle")
- `jwt_token` (secret): JWT token
- `jwt_role`: JWT role name
- `jwt_auth_path`: JWT auth mount path (default: "jwt")

### 2. AWS Secrets Engine Lookup Plugin (`vault_aws_lookup_plugin`)
Retrieves dynamic AWS credentials from Vault's AWS secrets engine.

**Supported Credential Types:**
- **IAM User Credentials** (`creds`): Standard AWS access keys
- **STS Assume Role** (`sts`): Temporary assume role credentials

**Lookup Configuration:**
- `mount_path`: AWS secrets engine mount path (default: "aws")
- `role_name` (required): AWS role name configured in Vault
- `credential_type`: Type of credentials ("creds" or "sts", default: "creds")
- `namespace` (optional): Vault Enterprise namespace for this specific lookup

**Returns AWS Credentials:**
- `access_key_id`: AWS access key ID
- `secret_access_key`: AWS secret access key
- `session_token`: AWS session token (for STS credentials)
- `arn`: ARN of the assumed role (for STS credentials)
- `credential_type`: Type of credential generated (for reference)
- `vault_role`: Vault role used (for reference)

## 🚀 Installation

### Prerequisites
- AWX or Ansible Automation Platform
- Access to all AWX/AAP execution nodes
- HashiCorp Vault server with appropriate secret engines enabled

### Installation Steps

1. **Install the plugin package on all AWX/AAP nodes:**

```bash
# Clone or download this repository
git clone https://github.com/your-repo/awx-vault-secrets-plugin.git
cd awx-vault-secrets-plugin

# Install in AWX Python environment
awx-python -m pip install .
```

2. **Register the plugins with AWX/AAP:**

```bash
awx-manage setup_managed_credential_types
```

3. **Restart AWX/AAP services:**

```bash
# For AWX
sudo systemctl restart awx-web awx-task

# For AAP
sudo systemctl restart automation-controller
```

4. **Verify installation:**
   - Log into AWX/AAP web interface
   - Navigate to **Credential Types**
   - Look for "HashiCorp Vault Authentication" and "Vault AWS Secrets Lookup"

## 🔧 Configuration & Usage

### Step 1: Create Vault Authentication Credential

1. In AWX/AAP, navigate to **Credentials** → **Add**
2. Select **HashiCorp Vault Authentication** as the credential type
3. Configure your Vault connection:

**Example - Token Authentication:**
```
Name: vault-prod-auth
Credential Type: HashiCorp Vault Authentication
URL: https://vault.company.com:8200
Namespace: production (optional, for Vault Enterprise)
Token: hvs.XXXXXXXXXX (your Vault token)
Verify SSL: ✓
```

**Example - AppRole Authentication:**
```
Name: vault-approle-auth
Credential Type: HashiCorp Vault Authentication
URL: https://vault.company.com:8200
Role ID: 12345678-1234-1234-1234-123456789abc
Secret ID: abcdefgh-abcd-abcd-abcd-abcdefghijkl
Auth Path: approle
```

### Step 2: Create AWS Lookup Credential

1. Navigate to **Credentials** → **Add**
2. Select **Vault AWS Secrets Lookup** as the credential type
3. Configure the lookup parameters:

```
Name: aws-dev-creds-lookup
Credential Type: Vault AWS Secrets Lookup
AWS Mount Path: aws
AWS Role Name: dev-ec2-role
Credential Type: creds
Namespace: development (optional override)
```

### Step 3: Use in Job Templates

1. Edit your **Job Template**
2. In the **Credentials** section, add:
   - Your Vault auth credential (from Step 1)
   - Your AWS lookup credential (from Step 2)
3. The plugins will automatically work together

### Step 4: Access Credentials in Playbooks

AWS credentials are automatically injected as environment variables and extra_vars:

```yaml
---
- name: Example playbook using dynamic AWS credentials
  hosts: localhost
  tasks:
    - name: Show available AWS credentials
      debug:
        msg: |
          AWS Access Key ID: {{ aws_access_key_id }}
          Credential Type: {{ aws_credential_type }}
          Vault Role: {{ vault_role }}
    
    - name: Use AWS CLI with dynamic credentials
      shell: aws s3 ls
      environment:
        AWS_ACCESS_KEY_ID: "{{ aws_access_key_id }}"
        AWS_SECRET_ACCESS_KEY: "{{ aws_secret_access_key }}"
        AWS_SESSION_TOKEN: "{{ aws_session_token }}"
    
    - name: Use with AWS modules
      amazon.aws.s3_bucket_info:
        aws_access_key: "{{ aws_access_key_id }}"
        aws_secret_key: "{{ aws_secret_access_key }}"
        security_token: "{{ aws_session_token }}"
```

## ⚙️ Vault Configuration Examples

### AWS Secrets Engine Setup

```bash
# Enable AWS secrets engine
vault secrets enable aws

# Configure root credentials
vault write aws/config/root \
    access_key=AKIA... \
    secret_key=xxxx... \
    region=us-east-1

# Create IAM user role
vault write aws/roles/dev-ec2-role \
    credential_type=iam_user \
    policy_document=-<<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeImages",
        "s3:ListBucket"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Create STS assume role
vault write aws/roles/prod-assume-role \
    credential_type=assumed_role \
    role_arns=arn:aws:iam::123456789012:role/MyRole \
    default_sts_ttl=3600 \
    max_sts_ttl=7200
```

### AppRole Authentication Setup

```bash
# Enable AppRole auth method
vault auth enable approle

# Create policy for AWS access
vault policy write aws-secrets-policy - <<EOF
path "aws/creds/*" {
  capabilities = ["read"]
}
path "aws/sts/*" {
  capabilities = ["read"]
}
EOF

# Create AppRole
vault write auth/approle/role/awx-aws-role \
    token_policies="aws-secrets-policy" \
    token_ttl=1h \
    token_max_ttl=4h \
    bind_secret_id=true

# Get Role ID (save for AWX credential)
vault read auth/approle/role/awx-aws-role/role-id

# Generate Secret ID (save for AWX credential)
vault write -f auth/approle/role/awx-aws-role/secret-id
```

## 🔒 Security Best Practices

### Authentication
- **Use AppRole or JWT** instead of long-lived tokens for automated systems
- **Rotate Secret IDs** regularly for AppRole authentication
- **Implement token TTL** appropriate for your execution patterns

### Network Security
- **Always use HTTPS** for Vault communication
- **Validate SSL certificates** in production (set `verify_ssl: true`)
- **Network segmentation** between AWX and Vault

### Vault Policies
```hcl
# Example least-privilege policy
path "aws/creds/dev-*" {
  capabilities = ["read"]
}

path "auth/token/lookup-self" {
  capabilities = ["read"]
}
```

### Monitoring & Auditing
- Enable Vault audit logging
- Monitor failed authentication attempts
- Set up alerts for unusual credential access patterns

## 🐛 Troubleshooting

### Common Issues

**1. Authentication Failed**
```
Error: Vault authentication failed: 403 permission denied
```
- Verify Vault URL and network connectivity
- Check token/AppRole credentials
- Confirm Vault policies allow required access

**2. Role Not Found**
```
Error: Failed to retrieve AWS credentials: role not found
```
- Verify AWS role exists: `vault list aws/roles`
- Check mount path configuration
- Confirm namespace if using Vault Enterprise

**3. SSL Certificate Errors**
```
Error: SSL verification failed
```
- For testing: Set `verify_ssl: false`
- For production: Add proper CA certificate
- Check certificate chain and hostname matching

### Debug Mode

Enable detailed logging in AWX:

```python
# In AWX settings.py or local settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'awx_vault_secrets_plugin': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Testing Plugin Structure

```bash
# Test plugin imports
python -c "
from awx_vault_secrets_plugin import vault_auth_plugin, vault_aws_lookup_plugin
print('✓ Plugins imported successfully')
print(f'Auth plugin: {vault_auth_plugin.name}')
print(f'AWS plugin: {vault_aws_lookup_plugin.name}')
"
```

## 🗂️ Repository Structure

```
awx_vault_secrets_plugin/
├── __init__.py                 # Plugin exports and main interface
├── vault_auth.py              # Vault authentication plugin
├── vault_aws_lookup.py        # AWS secrets engine lookup plugin
└── common/                    # Shared utilities
    ├── __init__.py
    ├── vault_client.py        # Vault HTTP client wrapper
    └── exceptions.py          # Custom exception classes

tests/                        # Test modules
└── test_plugins.py          # Plugin structure tests
```

## 🚧 Future Enhancements

- **Database Secrets Engine**: Dynamic database credentials
- **PKI Secrets Engine**: Certificate generation and management  
- **Additional Auth Methods**: Kubernetes, Azure, AWS auth
- **KV Secrets Engine**: Enhanced KV v1/v2 support with batch operations

## 📝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-secret-engine`
3. Follow the existing plugin patterns in the codebase
4. Add tests for new functionality
5. Update documentation
6. Submit a pull request

## 📄 License

Apache License 2.0 - see [LICENSE](LICENSE) file for details.

---

**Need help?** Open an issue or check the [AWX documentation](https://docs.ansible.com/automation-controller/latest/html/userguide/credential_plugins.html) for credential plugin development.
