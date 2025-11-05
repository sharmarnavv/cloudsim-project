# Blockchain Development Environment Setup

This document describes the blockchain development environment setup for the Real Blockchain Integration feature.

## Overview

The blockchain development environment includes:
- Web3.py for blockchain interaction
- eth-account for account management
- py-solc-x for smart contract compilation
- Ganache for local blockchain development
- Configuration management system
- Test account generation

## Quick Start

### 1. Install Dependencies

Python dependencies are already installed via `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 2. Install Ganache CLI (Node.js required)

```bash
npm install -g ganache-cli
```

### 3. Validate Setup

```bash
python validate_blockchain_setup.py
```

### 4. Start Development Environment

```bash
python blockchain_setup.py
```

## Configuration

### Environment Files

- `.env.example` - Template for environment variables
- `.kiro/blockchain/config.json` - Blockchain network configurations
- `.kiro/blockchain/test_accounts.json` - Generated test accounts

### Supported Networks

- **Development**: Local Ganache (Chain ID: 1337)
- **Testing**: Polygon Mumbai Testnet (Chain ID: 80001)
- **Production**: Polygon Mainnet (Chain ID: 137)

## Directory Structure

```
.kiro/blockchain/
├── config.json              # Network configurations
├── test_accounts.json       # Generated test accounts
├── contracts/               # Contract ABIs and deployments
├── deployments/             # Deployment records
└── cache.db                 # Local transaction cache (created at runtime)

contracts/
└── SchedulingContract.json  # Smart contract ABI (to be created)
```

## Usage

### Load Configuration

```python
from blockchain_config import get_blockchain_config

# Load development configuration
config = get_blockchain_config("development")
print(f"Network: {config.network_name}")
print(f"RPC URL: {config.rpc_url}")
```

### Start Ganache

```python
from blockchain_setup import GanacheManager
from blockchain_config import get_blockchain_config

config = get_blockchain_config("development")
ganache = GanacheManager(config)

# Start Ganache
if ganache.start_ganache():
    print("Ganache started successfully")
    accounts = ganache.get_accounts()
    print(f"Available accounts: {len(accounts)}")
```

## Validation

The `validate_blockchain_setup.py` script checks:
- ✅ Required dependencies are installed
- ✅ Configuration files are valid
- ✅ Directory structure exists
- ✅ Test accounts are generated
- ✅ Ganache connection (when running)

## Next Steps

After completing this setup, you can proceed to:
1. Implement blockchain manager infrastructure (Task 2)
2. Develop smart contract system (Task 3)
3. Build transaction management system (Task 4)

## Troubleshooting

### Ganache Not Found
```bash
npm install -g ganache-cli
```

### Port Already in Use
Change the port in configuration or stop the conflicting process:
```bash
netstat -ano | findstr :8545
```

### Web3 Connection Issues
Ensure Ganache is running and the RPC URL is correct in the configuration.