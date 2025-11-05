# Distributed Transaction Ledger for BlockchainInspiredScheduler

This implementation adds a comprehensive distributed transaction ledger to track all scheduling assignments made by the `BlockchainInspiredScheduler`. The ledger implements blockchain principles with immutable records, block structure, and cryptographic validation.

## Features

### 🔗 Blockchain Structure
- **Blocks**: Transactions are grouped into blocks with configurable size
- **Hashing**: Each block and transaction has cryptographic hashes (SHA-256)
- **Merkle Trees**: Blocks use merkle roots for transaction integrity
- **Chain Validation**: Full chain integrity validation with hash verification

### 📊 Transaction Tracking
- **Detailed Records**: Each scheduling decision is recorded with:
  - VM state before and after assignment
  - Task requirements and resource allocation
  - Scheduling scores and status (assigned/failed)
  - Timestamps and unique transaction IDs

### 📈 Analytics & Statistics
- **VM Performance**: Track assignment success rates per VM
- **Resource Utilization**: Monitor CPU, memory, I/O, and bandwidth allocation
- **System Overview**: Get comprehensive ledger statistics
- **Historical Analysis**: Query transaction history by VM or task

## Usage

### Basic Usage

```python
from schedulers import BlockchainInspiredScheduler, VM

# Create scheduler with distributed transaction ledger
vm_capacity = {'cpu': 8, 'mem': 16, 'io': 4, 'bw': 10}
scheduler = BlockchainInspiredScheduler(vm_capacity)

# Create VMs
vms = [VM(i, vm_capacity) for i in range(3)]

# Schedule tasks (automatically recorded in ledger)
task = {
    'id': 'task_001',
    'cpu': 2, 'mem': 4, 'io': 1, 'bw': 2,
    'deadline': time.time() + 3600
}

vm, score = scheduler.schedule(task, vms)
if vm:
    vm.assign(task)  # Apply the assignment
```

### Ledger Operations

```python
# Get comprehensive ledger statistics
stats = scheduler.get_ledger_stats()
print(f"Total transactions: {stats['total_transactions']}")
print(f"Success rate: {stats['success_rate']:.2%}")

# Get VM-specific statistics
vm_stats = scheduler.get_vm_ledger_history(vm_id=0)
print(f"VM 0 assignments: {vm_stats['total_assignments']}")

# Get recent transactions
recent = scheduler.get_recent_transactions(limit=5)
for tx in recent:
    print(f"Task {tx.task_id} -> VM {tx.vm_id} ({tx.status})")

# Validate ledger integrity
is_valid = scheduler.validate_ledger_integrity()
print(f"Chain integrity: {'✓ Valid' if is_valid else '✗ Invalid'}")

# Force mine pending transactions
scheduler.force_mine_pending_transactions()

# Export complete ledger data
ledger_data = scheduler.export_ledger_data()
```

### Transaction Structure

Each transaction contains:
```python
{
    'transaction_id': 'tx_1_1762306597918',
    'timestamp': 1762306597.918,
    'vm_id': 0,
    'task_id': 'task_001',
    'task_requirements': {'cpu': 2, 'mem': 4, 'io': 1, 'bw': 2},
    'vm_state_before': {'cpu': 0, 'mem': 0, 'io': 0, 'bw': 0},
    'vm_state_after': {'cpu': 2, 'mem': 4, 'io': 1, 'bw': 2},
    'score': 277.7778,
    'status': 'assigned',
    'block_hash': '508b7891fa12ef06...'
}
```

## Demo Scripts

### Run the Full Demo
```bash
python ledger_demo.py
```
This demonstrates:
- Scheduling multiple tasks across VMs
- Automatic ledger recording
- Block mining and validation
- Comprehensive statistics and analytics

### Run Basic Test
```bash
python test_ledger.py
```
Simple test to verify ledger functionality.

## Configuration

### Block Size
```python
# Create scheduler with custom block size
scheduler = BlockchainInspiredScheduler(vm_capacity)
scheduler.ledger.block_size = 10  # Transactions per block
```

### Ledger Features
- **Immutable Records**: Once transactions are in blocks, they cannot be modified
- **Automatic Mining**: Blocks are automatically created when reaching configured size
- **Integrity Validation**: Full cryptographic validation of the entire chain
- **Efficient Queries**: Fast lookups by VM ID, task ID, or time range

## Benefits

1. **Audit Trail**: Complete history of all scheduling decisions
2. **Performance Analysis**: Detailed metrics for optimization
3. **Debugging**: Track down scheduling issues with full context
4. **Compliance**: Immutable records for regulatory requirements
5. **Research**: Rich dataset for scheduling algorithm analysis

## Implementation Details

- **Hash Algorithm**: SHA-256 for all cryptographic operations
- **Merkle Trees**: Binary tree structure for transaction integrity
- **Block Structure**: Standard blockchain block format with headers
- **Storage**: In-memory storage (can be extended to persistent storage)
- **Validation**: Full chain validation including hash verification

The ledger provides enterprise-grade distributed transaction tracking while being lightweight enough for development and testing environments.