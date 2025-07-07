"""
Test file to verify plugin structure and basic functionality.
"""

import sys
import os

# Add the package to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def test_plugin_imports():
    """Test that plugins can be imported successfully."""
    try:
        from awx_vault_secrets_plugin import vault_auth_plugin, vault_aws_lookup_plugin
        print("✓ Plugin imports successful")
        return True
    except ImportError as e:
        print(f"✗ Plugin import failed: {e}")
        return False

def test_plugin_structure():
    """Test that plugins have the correct structure."""
    try:
        from awx_vault_secrets_plugin import vault_auth_plugin, vault_aws_lookup_plugin
        
        # Test auth plugin structure
        assert hasattr(vault_auth_plugin, 'name'), "Auth plugin missing name"
        assert hasattr(vault_auth_plugin, 'inputs'), "Auth plugin missing inputs"
        assert hasattr(vault_auth_plugin, 'backend'), "Auth plugin missing backend"
        assert callable(vault_auth_plugin.backend), "Auth plugin backend not callable"
        
        # Test AWS lookup plugin structure
        assert hasattr(vault_aws_lookup_plugin, 'name'), "AWS plugin missing name"
        assert hasattr(vault_aws_lookup_plugin, 'inputs'), "AWS plugin missing inputs"
        assert hasattr(vault_aws_lookup_plugin, 'backend'), "AWS plugin missing backend"
        assert callable(vault_aws_lookup_plugin.backend), "AWS plugin backend not callable"
        
        print("✓ Plugin structure validation successful")
        return True
    except Exception as e:
        print(f"✗ Plugin structure validation failed: {e}")
        return False

def test_plugin_inputs():
    """Test that plugin inputs have required fields."""
    try:
        from awx_vault_secrets_plugin import vault_auth_plugin, vault_aws_lookup_plugin
        
        # Test auth plugin inputs
        auth_inputs = vault_auth_plugin.inputs
        assert 'fields' in auth_inputs, "Auth plugin missing fields"
        assert 'required' in auth_inputs, "Auth plugin missing required fields"
        assert 'url' in auth_inputs['required'], "Auth plugin missing required URL"
        
        # Test AWS plugin inputs
        aws_inputs = vault_aws_lookup_plugin.inputs
        assert 'metadata' in aws_inputs, "AWS plugin missing metadata"
        assert 'required' in aws_inputs, "AWS plugin missing required fields"
        assert 'role_name' in aws_inputs['required'], "AWS plugin missing required role_name"
        
        print("✓ Plugin inputs validation successful")
        return True
    except Exception as e:
        print(f"✗ Plugin inputs validation failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing HashiCorp Vault Credential Plugins...")
    print("=" * 50)
    
    tests = [
        test_plugin_imports,
        test_plugin_structure,
        test_plugin_inputs
    ]
    
    results = []
    for test in tests:
        results.append(test())
        print()
    
    if all(results):
        print("🎉 All tests passed! Plugin structure is valid.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)
