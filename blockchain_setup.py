"""
Blockchain Development Environment Setup

This module provides utilities for setting up and managing the local blockchain
development environment using Ganache.
"""

import subprocess
import sys
import time
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
import requests
from web3 import Web3
from eth_account import Account
from blockchain_config import get_blockchain_config, BlockchainConfig

class GanacheManager:
    """Manages local Ganache blockchain instance"""
    
    def __init__(self, config: BlockchainConfig):
        self.config = config
        self.process = None
        self.accounts = []
        
    def start_ganache(self, accounts: int = 10, mnemonic: str = None) -> bool:
        """Start Ganache CLI with specified configuration"""
        
        # Check if Ganache is already running
        if self.is_running():
            print("Ganache is already running")
            return True
        
        # Try different ways to find ganache-cli on Windows
        ganache_commands = ["ganache-cli", "ganache-cli.cmd", "npx ganache-cli"]
        
        for ganache_cmd in ganache_commands:
            # Build Ganache command
            if ganache_cmd.startswith("npx"):
                cmd = [
                    "npx", "ganache-cli",
                    "--host", "127.0.0.1",
                    "--port", str(self._extract_port()),
                    "--networkId", str(self.config.chain_id),
                    "--accounts", str(accounts),
                    "--defaultBalanceEther", "1000",
                    "--gasLimit", str(self.config.gas_limit),
                    "--gasPrice", "20000000000",  # 20 gwei
                    "--quiet"
                ]
            else:
                cmd = [
                    ganache_cmd,
                    "--host", "127.0.0.1",
                    "--port", str(self._extract_port()),
                    "--networkId", str(self.config.chain_id),
                    "--accounts", str(accounts),
                    "--defaultBalanceEther", "1000",
                    "--gasLimit", str(self.config.gas_limit),
                    "--gasPrice", "20000000000",  # 20 gwei
                    "--quiet"
                ]
            
            if mnemonic:
                cmd.extend(["--mnemonic", mnemonic])
            
            try:
                print(f"Trying to start Ganache with: {' '.join(cmd)}")
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    shell=True  # Use shell on Windows
                )
                
                # Wait for Ganache to start
                if self._wait_for_startup():
                    self._load_accounts()
                    print(f"Ganache started successfully on {self.config.rpc_url}")
                    return True
                else:
                    print(f"Failed to start Ganache with {ganache_cmd}")
                    if self.process:
                        self.process.terminate()
                        self.process = None
                    continue
                    
            except FileNotFoundError:
                print(f"Command not found: {ganache_cmd}")
                continue
            except Exception as e:
                print(f"Error starting Ganache with {ganache_cmd}: {e}")
                continue
        
        print("Error: Could not start ganache-cli with any method.")
        print("Please ensure ganache-cli is installed: npm install -g ganache-cli")
        print("Or try running manually: ganache-cli --host 127.0.0.1 --port 8545")
        return False
    
    def stop_ganache(self):
        """Stop the Ganache process"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None
            print("Ganache stopped")
    
    def is_running(self) -> bool:
        """Check if Ganache is running"""
        try:
            response = requests.post(
                self.config.rpc_url,
                json={"jsonrpc": "2.0", "method": "web3_clientVersion", "id": 1},
                timeout=2
            )
            return response.status_code == 200
        except:
            return False
    
    def get_accounts(self) -> List[Dict[str, str]]:
        """Get list of available accounts"""
        return self.accounts
    
    def _extract_port(self) -> int:
        """Extract port from RPC URL"""
        try:
            return int(self.config.rpc_url.split(':')[-1])
        except:
            return 8545
    
    def _wait_for_startup(self, timeout: int = 30) -> bool:
        """Wait for Ganache to start up"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_running():
                return True
            time.sleep(1)
        return False
    
    def _load_accounts(self):
        """Load account information from Ganache"""
        try:
            w3 = Web3(Web3.HTTPProvider(self.config.rpc_url))
            accounts = w3.eth.accounts
            
            self.accounts = []
            for i, address in enumerate(accounts):
                balance = w3.eth.get_balance(address)
                self.accounts.append({
                    "index": i,
                    "address": address,
                    "balance": w3.from_wei(balance, 'ether'),
                    "private_key": f"0x{'0' * 63}{i+1:x}"  # Simplified for development
                })
                
        except Exception as e:
            print(f"Warning: Could not load account information: {e}")

class DevelopmentSetup:
    """Handles complete development environment setup"""
    
    def __init__(self):
        self.config = get_blockchain_config("development")
        self.ganache = GanacheManager(self.config)
        
    def setup_directories(self):
        """Create necessary directories for blockchain development"""
        directories = [
            ".kiro/blockchain",
            ".kiro/blockchain/contracts",
            ".kiro/blockchain/deployments",
            "contracts"
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
    
    def install_dependencies(self):
        """Install Python dependencies"""
        try:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
            ])
            print("Python dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error installing dependencies: {e}")
            return False
    
    def check_node_dependencies(self):
        """Check if Node.js dependencies are available"""
        ganache_commands = ["ganache-cli", "ganache-cli.cmd", "npx ganache-cli"]
        
        for cmd in ganache_commands:
            try:
                if cmd.startswith("npx"):
                    result = subprocess.check_output(
                        ["npx", "ganache-cli", "--version"], 
                        stderr=subprocess.STDOUT, 
                        shell=True
                    )
                else:
                    result = subprocess.check_output(
                        [cmd, "--version"], 
                        stderr=subprocess.STDOUT,
                        shell=True
                    )
                print(f"ganache-cli is available via: {cmd}")
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        
        print("ganache-cli not found with any method.")
        print("Install with: npm install -g ganache-cli")
        print("Or ensure Node.js and npm are properly installed")
        return False
    
    def create_sample_env(self):
        """Create sample .env file with blockchain configuration"""
        env_content = """# Blockchain Configuration
BLOCKCHAIN_ENV=development

# Development Network (Ganache)
GANACHE_RPC_URL=http://127.0.0.1:8545
GANACHE_CHAIN_ID=1337

# Test Networks
MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com
POLYGON_RPC_URL=https://polygon-rpc.com

# Security (DO NOT commit real private keys)
PRIVATE_KEY_PATH=.kiro/blockchain/private_key.enc
"""
        
        env_path = Path(".env.example")
        if not env_path.exists():
            with open(env_path, 'w') as f:
                f.write(env_content)
            print("Created .env.example file")
    
    def generate_test_accounts(self, count: int = 5) -> List[Dict[str, str]]:
        """Generate test accounts for development"""
        accounts = []
        
        for i in range(count):
            account = Account.create()
            accounts.append({
                "index": i,
                "address": account.address,
                "private_key": account.key.hex()
            })
        
        # Save to file for development use
        accounts_file = Path(".kiro/blockchain/test_accounts.json")
        with open(accounts_file, 'w') as f:
            json.dump(accounts, f, indent=2)
        
        print(f"Generated {count} test accounts saved to {accounts_file}")
        return accounts
    
    def setup_complete_environment(self) -> bool:
        """Set up complete blockchain development environment"""
        print("Setting up blockchain development environment...")
        
        # 1. Create directories
        self.setup_directories()
        
        # 2. Create sample environment file
        self.create_sample_env()
        
        # 3. Check dependencies
        if not self.check_node_dependencies():
            print("Please install Node.js dependencies first")
            return False
        
        # 4. Install Python dependencies
        if not self.install_dependencies():
            return False
        
        # 5. Generate test accounts
        self.generate_test_accounts()
        
        # 6. Start Ganache
        if self.ganache.start_ganache():
            print("\n✅ Blockchain development environment setup complete!")
            print(f"Ganache running on: {self.config.rpc_url}")
            print(f"Chain ID: {self.config.chain_id}")
            print(f"Available accounts: {len(self.ganache.get_accounts())}")
            return True
        else:
            print("❌ Failed to start Ganache")
            return False
    
    def cleanup(self):
        """Clean up development environment"""
        self.ganache.stop_ganache()

def main():
    """Main setup function"""
    setup = DevelopmentSetup()
    
    try:
        success = setup.setup_complete_environment()
        if success:
            print("\nDevelopment environment is ready!")
            print("You can now run blockchain integration tests.")
        else:
            print("\nSetup failed. Please check the error messages above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        setup.cleanup()
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error during setup: {e}")
        setup.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()