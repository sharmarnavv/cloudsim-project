#!/usr/bin/env python3
"""
Demonstration of the distributed transaction ledger integrated with BlockchainInspiredScheduler.
This script shows how scheduling assignments are tracked in an immutable ledger.
"""

from schedulers import BlockchainInspiredScheduler, VM
import time
import json

def create_sample_task(task_id: str, cpu: int = 2, mem: int = 4, io: int = 1, bw: int = 2, deadline: float = None):
    """Create a sample task for testing"""
    if deadline is None:
        deadline = time.time() + 3600  # 1 hour from now
    
    return {
        'id': task_id,
        'cpu': cpu,
        'mem': mem,
        'io': io,
        'bw': bw,
        'deadline': deadline
    }

def print_ledger_summary(scheduler):
    """Print a summary of the ledger state"""
    stats = scheduler.get_ledger_stats()
    print("\n" + "="*60)
    print("DISTRIBUTED TRANSACTION LEDGER SUMMARY")
    print("="*60)
    print(f"Total Blocks: {stats['total_blocks']}")
    print(f"Total Transactions: {stats['total_transactions']}")
    print(f"Pending Transactions: {stats['pending_transactions']}")
    print(f"Successful Assignments: {stats['successful_assignments']}")
    print(f"Failed Assignments: {stats['failed_assignments']}")
    print(f"Success Rate: {stats['success_rate']:.2%}")
    print(f"Chain Integrity: {'✓ Valid' if stats['chain_integrity'] else '✗ Invalid'}")
    print(f"Latest Block Hash: {stats['latest_block_hash'][:16]}..." if stats['latest_block_hash'] else "None")

def print_vm_stats(scheduler, vm_id):
    """Print detailed statistics for a specific VM"""
    stats = scheduler.get_vm_ledger_history(vm_id)
    print(f"\n--- VM {vm_id} Statistics ---")
    print(f"Total Assignments: {stats['total_assignments']}")
    print(f"Failed Assignments: {stats['failed_assignments']}")
    print(f"Success Rate: {stats['success_rate']:.2%}")
    print(f"Average Score: {stats['average_score']:.4f}")
    print(f"Total CPU Allocated: {stats['total_cpu_allocated']}")
    print(f"Total Memory Allocated: {stats['total_mem_allocated']}")

def print_recent_transactions(scheduler, limit=5):
    """Print recent transactions from the ledger"""
    transactions = scheduler.get_recent_transactions(limit)
    print(f"\n--- Last {len(transactions)} Transactions ---")
    for tx in transactions:
        status_symbol = "✓" if tx.status == "assigned" else "✗"
        print(f"{status_symbol} {tx.transaction_id}: Task {tx.task_id} -> VM {tx.vm_id} "
              f"(Score: {tx.score:.4f}, Status: {tx.status})")

def main():
    """Main demonstration function"""
    print("Distributed Transaction Ledger Demo for BlockchainInspiredScheduler")
    print("=" * 60)
    
    # Create scheduler with distributed transaction ledger
    vm_capacity = {'cpu': 8, 'mem': 16, 'io': 4, 'bw': 10}
    scheduler = BlockchainInspiredScheduler(vm_capacity)
    
    # Create VMs
    vms = [VM(i, vm_capacity) for i in range(3)]
    print(f"Created {len(vms)} VMs with capacity: {vm_capacity}")
    
    # Create and schedule multiple tasks
    tasks = [
        create_sample_task("task_001", cpu=2, mem=4, io=1, bw=2),
        create_sample_task("task_002", cpu=3, mem=6, io=2, bw=3),
        create_sample_task("task_003", cpu=1, mem=2, io=1, bw=1),
        create_sample_task("task_004", cpu=4, mem=8, io=2, bw=4),
        create_sample_task("task_005", cpu=2, mem=3, io=1, bw=2),
        create_sample_task("task_006", cpu=5, mem=10, io=3, bw=5),
        create_sample_task("task_007", cpu=1, mem=1, io=1, bw=1),
        create_sample_task("task_008", cpu=3, mem=5, io=2, bw=3),
    ]
    
    print(f"\nScheduling {len(tasks)} tasks...")
    
    # Schedule tasks and track assignments
    successful_assignments = 0
    for i, task in enumerate(tasks):
        print(f"\nScheduling Task {task['id']}...")
        vm, score = scheduler.schedule(task, vms)
        
        if vm:
            vm.assign(task)
            successful_assignments += 1
            print(f"  ✓ Assigned to VM {vm.id} with score {score:.4f}")
            print(f"  VM {vm.id} new load: CPU={vm.cpu}/{vm.capacity['cpu']}, "
                  f"MEM={vm.mem}/{vm.capacity['mem']}")
        else:
            print(f"  ✗ Failed to assign task {task['id']}")
        
        # Force mine a block every few transactions for demo
        if (i + 1) % 3 == 0:
            scheduler.force_mine_pending_transactions()
            print("  📦 Mined new block with recent transactions")
    
    # Force mine any remaining pending transactions
    scheduler.force_mine_pending_transactions()
    
    # Display comprehensive results
    print_ledger_summary(scheduler)
    
    # Show VM-specific statistics
    for vm in vms:
        print_vm_stats(scheduler, vm.id)
    
    # Show recent transactions
    print_recent_transactions(scheduler, limit=8)
    
    # Validate ledger integrity
    print(f"\n🔍 Ledger Integrity Check: {'✓ PASSED' if scheduler.validate_ledger_integrity() else '✗ FAILED'}")
    
    # Export ledger data (sample)
    print("\n📊 Exporting ledger data...")
    ledger_data = scheduler.export_ledger_data()
    print(f"Exported {len(ledger_data['blocks'])} blocks and {len(ledger_data['pending_transactions'])} pending transactions")
    
    # Show a sample transaction in detail
    if ledger_data['blocks']:
        sample_block = ledger_data['blocks'][-1]  # Last block
        if sample_block['transactions']:
            sample_tx = sample_block['transactions'][0]
            print(f"\n📋 Sample Transaction Detail:")
            print(f"  Transaction ID: {sample_tx['transaction_id']}")
            print(f"  VM ID: {sample_tx['vm_id']}")
            print(f"  Task ID: {sample_tx['task_id']}")
            print(f"  Status: {sample_tx['status']}")
            print(f"  Score: {sample_tx['score']:.4f}")
            print(f"  Block Hash: {sample_tx['block_hash'][:16]}...")
            print(f"  VM State Before: {sample_tx['vm_state_before']}")
            print(f"  VM State After: {sample_tx['vm_state_after']}")

if __name__ == "__main__":
    main()