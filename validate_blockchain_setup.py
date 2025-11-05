"""
Blockchain Setup Validation Script

This script validates that the blockchain development environment
is properly configured and working.
"""

import sys
from pathlib import Path
from web3 import Web3
from blockchain_config import get_blockchain_config
from blockchain_setup import GanacheManager

def validate_dependencies():
    """Validate that required dependencies are installed"""
    print("Validating dependencies...")
    
    try:
        import web3
        print(f"✅ web3.py version: {web3.__version__}")
    except ImportError:
        print("❌ web3.py not installed")
        return False
    
    try:
        import eth_account
        print(f"✅ eth-account available")
    except ImportError:
        print("❌ eth-account not installed")
        return False
    
    try:
        from solcx import get_solc_version
        print(f"✅ py-solc-x available")
    except ImportError:
        print("❌ py-solc-x not installed")
        return False
    
    return True

def validate_configuration():
    """Validate blockchain configuration"""
    print("\nValidating configuration...")
    
    try:
        config = get_blockchain_config("development")
        print(f"✅ Configuration loaded for network: {config.network_name}")
        print(f"   RPC URL: {config.rpc_url}")
        print(f"   Chain ID: {config.chain_id}")
        return True
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def validate_directories():
    """Validate that required directories exist"""
    print("\nValidating directories...")
    
    required_dirs = [
        ".kiro/blockchain",
        ".kiro/blockchain/contracts",
        ".kiro/blockchain/deployments",
        "contracts"
    ]
    
    all_exist = True
    for directory in required_dirs:
        if Path(directory).exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            all_exist = False
    
    return all_exist

def validate_ganache_connection():
    """Validate connection to Ganache"""
    print("\nValidating Ganache connection...")
    
    config = get_blockchain_config("development")
    ganache = GanacheManager(config)
    
    if ganache.is_running():
        print("✅ Ganache is running")
        
        try:
            w3 = Web3(Web3.HTTPProvider(config.rpc_url))
            if w3.is_connected():
                print("✅ Web3 connection successful")
                
                # Get network info
                chain_id = w3.eth.chain_id
                block_number = w3.eth.block_number
                accounts = w3.eth.accounts
                
                print(f"   Chain ID: {chain_id}")
                print(f"   Latest block: {block_number}")
                print(f"   Available accounts: {len(accounts)}")
                
                # Test account balance
                if accounts:
                    balance = w3.eth.get_balance(accounts[0])
                    balance_eth = w3.from_wei(balance, 'ether')
                    print(f"   First account balance: {balance_eth} ETH")
                
                return True
            else:
                print("❌ Web3 connection failed")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    else:
        print("❌ Ganache is not running")
        print("   Start Ganache with: python blockchain_setup.py")
        return False

def validate_test_accounts():
    """Validate test accounts file"""
    print("\nValidating test accounts...")
    
    accounts_file = Path(".kiro/blockchain/test_accounts.json")
    if accounts_file.exists():
        try:
            import json
            with open(accounts_file, 'r') as f:
                accounts = json.load(f)
            print(f"✅ Test accounts file exists with {len(accounts)} accounts")
            return True
        except Exception as e:
            print(f"❌ Error reading test accounts: {e}")
            return False
    else:
        print("❌ Test accounts file not found")
        return False

def main():
    """Main validation function"""
    print("🔍 Validating Blockchain Development Environment\n")
    
    validations = [
        ("Dependencies", validate_dependencies),
        ("Configuration", validate_configuration),
        ("Directories", validate_directories),
        ("Test Accounts", validate_test_accounts),
        ("Ganache Connection", validate_ganache_connection),
    ]
    
    results = []
    for name, validator in validations:
        try:
            result = validator()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} validation failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*50)
    print("VALIDATION SUMMARY")
    print("="*50)
    
    passed = 0
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)}")
    
    if passed == len(results):
        print("\n🎉 All validations passed! Blockchain environment is ready.")
        return True
    else:
        print(f"\n⚠️  {len(results) - passed} validation(s) failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)