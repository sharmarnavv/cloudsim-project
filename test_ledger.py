#!/usr/bin/env python3
"""
Simple test to verify the distributed transaction ledger functionality.
"""

from schedulers import BlockchainInspiredScheduler, VM
import time

def test_basic_ledger():
    """Test basic ledger functionality"""
    print("Testing basic ledger functionality...")
    
    # Create scheduler
    vm_capacity = {'cpu': 8, 'mem': 16, 'io': 4, 'bw': 10}
    scheduler = BlockchainInspiredScheduler(vm_capacity)
    
    # Create VMs
    vms = [VM(0, vm_capacity), VM(1, vm_capacity)]
    
    # Create simple task
    task = {
        'id': 'test_task_001',
        'cpu': 2,
        'mem': 4,
        'io': 1,
        'bw': 2,
        'deadline': time.time() + 3600
    }
    
    print(f"Initial ledger integrity: {scheduler.validate_ledger_integrity()}")
    
    # Schedule task
    vm, score = scheduler.schedule(task, vms)
    if vm:
        vm.assign(task)
        print(f"Task assigned to VM {vm.id}")
    
    # Force mine block
    scheduler.force_mine_pending_transactions()
    
    # Check integrity
    print(f"Final ledger integrity: {scheduler.validate_ledger_integrity()}")
    
    # Get stats
    stats = scheduler.get_ledger_stats()
    print(f"Total transactions: {stats['total_transactions']}")
    print(f"Total blocks: {stats['total_blocks']}")
    
    return scheduler.validate_ledger_integrity()

if __name__ == "__main__":
    success = test_basic_ledger()
    print(f"Test {'PASSED' if success else 'FAILED'}")