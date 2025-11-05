"""
Blockchain Configuration Management System

This module provides configuration management for blockchain integration,
supporting different networks and environments.
"""

import os
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class BlockchainConfig:
    """Configuration class for blockchain network settings"""
    
    # Network configuration
    network_name: str = "ganache"
    rpc_url: str = "http://127.0.0.1:8545"
    chain_id: int = 1337
    
    # Contract configuration
    contract_address: Optional[str] = None
    contract_abi_path: str = "contracts/SchedulingContract.json"
    
    # Security configuration
    private_key_path: str = ".kiro/blockchain/private_key.enc"
    wallet_address: Optional[str] = None
    
    # Transaction configuration
    gas_limit: int = 500000
    gas_price_gwei: Optional[int] = None  # Auto-estimate if None
    confirmation_blocks: int = 1  # Lower for development
    
    # Performance configuration
    batch_size: int = 10
    batch_timeout: int = 300  # seconds
    
    # Fallback configuration
    fallback_enabled: bool = True
    cache_enabled: bool = True
    cache_db_path: str = ".kiro/blockchain/cache.db"
    
    # Development configuration
    auto_deploy_contract: bool = True
    use_test_accounts: bool = True
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if self.chain_id <= 0:
            raise ValueError("Chain ID must be positive")
        if self.gas_limit <= 0:
            raise ValueError("Gas limit must be positive")
        if self.batch_size <= 0:
            raise ValueError("Batch size must be positive")

class ConfigManager:
    """Manages blockchain configuration for different environments"""
    
    def __init__(self, config_path: str = ".kiro/blockchain/config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
    def load_config(self, environment: str = "development") -> BlockchainConfig:
        """Load configuration for specified environment"""
        
        # Try to load from file first
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                    env_config = config_data.get(environment, {})
                    return BlockchainConfig(**env_config)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Could not load config from {self.config_path}: {e}")
        
        # Return default configuration based on environment
        return self._get_default_config(environment)
    
    def save_config(self, config: BlockchainConfig, environment: str = "development"):
        """Save configuration to file"""
        
        # Load existing config file or create new one
        config_data = {}
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
            except json.JSONDecodeError:
                config_data = {}
        
        # Update with new configuration
        config_data[environment] = self._config_to_dict(config)
        
        # Save to file
        with open(self.config_path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    def _get_default_config(self, environment: str) -> BlockchainConfig:
        """Get default configuration for environment"""
        
        if environment == "development":
            return BlockchainConfig(
                network_name="ganache",
                rpc_url="http://127.0.0.1:8545",
                chain_id=1337,
                confirmation_blocks=1,
                use_test_accounts=True,
                auto_deploy_contract=True
            )
        elif environment == "testing":
            return BlockchainConfig(
                network_name="polygon-mumbai",
                rpc_url=os.getenv("MUMBAI_RPC_URL", "https://rpc-mumbai.maticvigil.com"),
                chain_id=80001,
                confirmation_blocks=3,
                use_test_accounts=True,
                auto_deploy_contract=False
            )
        elif environment == "production":
            return BlockchainConfig(
                network_name="polygon",
                rpc_url=os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com"),
                chain_id=137,
                confirmation_blocks=5,
                use_test_accounts=False,
                auto_deploy_contract=False,
                gas_price_gwei=30  # Conservative gas price for mainnet
            )
        else:
            raise ValueError(f"Unknown environment: {environment}")
    
    def _config_to_dict(self, config: BlockchainConfig) -> Dict[str, Any]:
        """Convert BlockchainConfig to dictionary for JSON serialization"""
        return {
            "network_name": config.network_name,
            "rpc_url": config.rpc_url,
            "chain_id": config.chain_id,
            "contract_address": config.contract_address,
            "contract_abi_path": config.contract_abi_path,
            "private_key_path": config.private_key_path,
            "wallet_address": config.wallet_address,
            "gas_limit": config.gas_limit,
            "gas_price_gwei": config.gas_price_gwei,
            "confirmation_blocks": config.confirmation_blocks,
            "batch_size": config.batch_size,
            "batch_timeout": config.batch_timeout,
            "fallback_enabled": config.fallback_enabled,
            "cache_enabled": config.cache_enabled,
            "cache_db_path": config.cache_db_path,
            "auto_deploy_contract": config.auto_deploy_contract,
            "use_test_accounts": config.use_test_accounts
        }

# Global configuration manager instance
config_manager = ConfigManager()

def get_blockchain_config(environment: str = None) -> BlockchainConfig:
    """Get blockchain configuration for current environment"""
    if environment is None:
        environment = os.getenv("BLOCKCHAIN_ENV", "development")
    
    return config_manager.load_config(environment)

def update_blockchain_config(config: BlockchainConfig, environment: str = None):
    """Update blockchain configuration"""
    if environment is None:
        environment = os.getenv("BLOCKCHAIN_ENV", "development")
    
    config_manager.save_config(config, environment)