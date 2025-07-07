#!/usr/bin/env python3
"""
Test plugin registration and structure for AWX credential plugins.

This script verifies that plugins are properly structured for AWX auto-registration.
"""

import sys

def test_plugin_registration():
    """Test that plugins are properly structured for AWX registration."""
    print("🔍 Testing plugin registration structure...")
    
    try:
        # Import plugins
        from awx_vault_secrets_plugin import vault_auth_plugin, vault_aws_lookup_plugin
        
        # Test plugin structure
        plugins = {
            'vault_auth': vault_auth_plugin,
            'vault_aws_lookup': vault_aws_lookup_plugin
        }
        
        for name, plugin in plugins.items():
            print(f"\n📋 {name} plugin:")
            print(f"  Name: {plugin.name}")
            print(f"  Has inputs: {'✓' if hasattr(plugin, 'inputs') else '✗'}")
            print(f"  Has backend: {'✓' if hasattr(plugin, 'backend') else '✗'}")
            
            # Check inputs structure
            inputs = plugin.inputs
            print(f"  Fields: {len(inputs.get('fields', []))}")
            print(f"  Metadata: {len(inputs.get('metadata', []))}")
            print(f"  Required: {inputs.get('required', [])}")
            
            # Validate required structure for AWX
            if not isinstance(inputs, dict):
                raise ValueError(f"{name}: inputs must be a dict")
            if 'fields' not in inputs:
                raise ValueError(f"{name}: inputs must have 'fields' key")
            if not isinstance(inputs['fields'], list):
                raise ValueError(f"{name}: fields must be a list")
                
        print("\n✅ All plugins have valid structure for AWX registration!")
        return True
        
    except Exception as e:
        print(f"\n❌ Plugin registration test failed: {e}")
        return False

def test_entry_points():
    """Test that entry points are correctly configured."""
    print("\n🔍 Testing entry point configuration...")
    
    try:
        import pkg_resources
        
        # This simulates what AWX does when loading plugins
        entry_points = list(pkg_resources.iter_entry_points('awx.credential_plugins'))
        
        if not entry_points:
            print("⚠️  No entry points found - this is normal if package isn't installed")
            print("   Run: pip install -e . to test entry points")
            return True
            
        print(f"Found {len(entry_points)} entry points:")
        for ep in entry_points:
            print(f"  - {ep.name}: {ep.module_name}")
            # Try to load the entry point
            plugin = ep.load()
            print(f"    Loaded: {plugin.name}")
            
        print("✅ Entry points configuration is valid!")
        return True
        
    except Exception as e:
        print(f"❌ Entry point test failed: {e}")
        return False

def show_registration_command():
    """Show the command needed to register plugins with AWX."""
    print("\n" + "="*60)
    print("📝 TO REGISTER PLUGINS WITH AWX:")
    print("="*60)
    print()
    print("1. Install the package:")
    print("   awx-python -m pip install /path/to/this/directory")
    print()
    print("2. Register plugins:")
    print("   awx-manage setup_managed_credential_types")
    print()
    print("3. Restart AWX services:")
    print("   systemctl restart awx-web awx-task")
    print()
    print("4. Check AWX UI for new credential types:")
    print("   - HashiCorp Vault Authentication")
    print("   - HashiCorp Vault AWS Secrets Engine Lookup")
    print()

if __name__ == "__main__":
    print("AWX Vault Plugin Registration Test")
    print("=" * 50)
    
    success = True
    success &= test_plugin_registration()
    success &= test_entry_points()
    
    show_registration_command()
    
    if success:
        print("\n🎉 All tests passed! Plugins ready for AWX registration.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check errors above.")
        sys.exit(1)
