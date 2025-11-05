from typing import List, Dict, Tuple, Optional
import heapq
from collections import deque
import time
import hashlib
import json
from dataclasses import dataclass, asdict

class VM:
    def __init__(self, id: int, capacity: Dict[str, int]):
        self.id = id
        self.capacity = capacity
        self.cpu = 0
        self.mem = 0
        self.io = 0
        self.bw = 0
        self.tasks = []

    def can_assign(self, task: Dict) -> bool:
        return (
            self.cpu + task['cpu'] <= self.capacity['cpu'] and
            self.mem + task['mem'] <= self.capacity['mem'] and
            self.io + task['io'] <= self.capacity['io'] and
            self.bw + task['bw'] <= self.capacity['bw']
        )

    def assign(self, task: Dict) -> None:
        self.cpu += task['cpu']
        self.mem += task['mem']
        self.io += task['io']
        self.bw += task['bw']
        self.tasks.append(task['id'])

    def load_score(self) -> float:
        return (
            self.cpu / self.capacity['cpu'] +
            self.mem / self.capacity['mem'] +
            self.io / self.capacity['io'] +
            self.bw / self.capacity['bw']
        ) / 4

class Scheduler:
    def __init__(self, vm_capacity: Dict[str, int]):
        self.vm_capacity = vm_capacity

    def create_vms(self, num_vms: int) -> List[VM]:
        return [VM(i, self.vm_capacity) for i in range(num_vms)]

class RoundRobinScheduler(Scheduler):
    def __init__(self, vm_capacity: Dict[str, int]):
        super().__init__(vm_capacity)
        self.current_vm_index = 0
        self._vm_count = 0
        print(f"RoundRobinScheduler created: {id(self)}")

    def schedule(self, task: Dict, vms: List[VM]) -> Tuple[Optional[VM], float]:
        num_vms = len(vms)
        if num_vms == 0:
            return None, 0
            
        # Reset index if number of VMs has changed
        if self._vm_count != num_vms:
            self._vm_count = num_vms
            self.current_vm_index = 0

        # Store starting index
        start_index = self.current_vm_index

        for _ in range(num_vms):
            vm = vms[self.current_vm_index]
            self.current_vm_index = (self.current_vm_index + 1) % num_vms
            
            if vm.can_assign(task):
                return vm, vm.load_score()

        # Reset to where we started if no VM found
        self.current_vm_index = start_index
        return None, 0

class UrgencyAwareScheduler(Scheduler):
    def __init__(self, vm_capacity: Dict[str, int]):
        super().__init__(vm_capacity)
        print(f"UrgencyAwareScheduler created: {id(self)}")
        
    def calculate_score(self, task: Dict, vm: VM) -> float:
        load_factor = vm.load_score()
        return task['deadline'] + load_factor * 5

    def schedule(self, task: Dict, vms: List[VM]) -> Tuple[Optional[VM], float]:
        heap = []
        for vm in vms:
            if vm.can_assign(task):
                score = self.calculate_score(task, vm)
                heapq.heappush(heap, (score, vm.id, vm))
        
        if heap:
            score, _, vm = heapq.heappop(heap)
            return vm, score
        return None, float('inf')

class LeastLoadedScheduler(Scheduler):
    def __init__(self, vm_capacity: Dict[str, int]):
        super().__init__(vm_capacity)
        print(f"LeastLoadedScheduler created: {id(self)}")
        self.last_assigned_vm = None  # Track last assignment for better load distribution

    def schedule(self, task: Dict, vms: List[VM]) -> Tuple[Optional[VM], float]:
        idle_vms = [vm for vm in vms if vm.can_assign(task) and vm.load_score() == 0]
        if idle_vms:
            chosen_vm = idle_vms  
            return chosen_vm[0], 0
        else:
            best_vm = None
            min_load = float('inf')
            for vm in vms:
                if vm.can_assign(task):
                    load = vm.load_score()
                    if load < min_load:
                        min_load = load
                        best_vm = vm
            return best_vm, min_load if best_vm else float('inf')

@dataclass
class SchedulingTransaction:
    """Represents a single scheduling transaction in the ledger"""
    transaction_id: str
    timestamp: float
    vm_id: int
    task_id: str
    task_requirements: Dict[str, int]
    vm_state_before: Dict[str, int]
    vm_state_after: Dict[str, int]
    score: float
    status: str  # 'assigned', 'failed', 'rejected'
    block_hash: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass 
class LedgerBlock:
    """Represents a block in the fake blockchain ledger"""
    block_id: int
    timestamp: float
    transactions: List[SchedulingTransaction]
    previous_hash: str
    merkle_root: str
    block_hash: str = ""
    
    def calculate_merkle_root(self) -> str:
        """Calculate merkle root of all transactions in the block"""
        if not self.transactions:
            return hashlib.sha256("empty_block".encode()).hexdigest()
        
        tx_hashes = [self._hash_transaction(tx) for tx in self.transactions]
        
        # Simple merkle tree implementation
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])  # Duplicate last hash if odd number
            
            new_level = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            tx_hashes = new_level
        
        return tx_hashes[0]
    
    def _hash_transaction(self, tx: SchedulingTransaction) -> str:
        """Create hash of a transaction (excluding block_hash field)"""
        tx_dict = tx.to_dict()
        # Remove block_hash from the hash calculation to avoid circular dependency
        tx_dict.pop('block_hash', None)
        tx_data = json.dumps(tx_dict, sort_keys=True)
        return hashlib.sha256(tx_data.encode()).hexdigest()
    
    def calculate_block_hash(self) -> str:
        """Calculate hash of the entire block"""
        block_data = {
            'block_id': self.block_id,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'transaction_count': len(self.transactions)
        }
        block_string = json.dumps(block_data, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

class DistributedTransactionLedger:
    """
    Distributed transaction ledger for tracking scheduling assignments.
    Provides immutable record keeping with cryptographic validation and block structure.
    """
    
    def __init__(self, block_size: int = 10):
        self.blocks: List[LedgerBlock] = []
        self.pending_transactions: List[SchedulingTransaction] = []
        self.block_size = block_size
        self.transaction_counter = 0
        
        # Create genesis block
        self._create_genesis_block()
    
    def _create_genesis_block(self):
        """Create the first block in the chain"""
        genesis_block = LedgerBlock(
            block_id=0,
            timestamp=time.time(),
            transactions=[],
            previous_hash="0" * 64,
            merkle_root=""
        )
        genesis_block.merkle_root = genesis_block.calculate_merkle_root()
        genesis_block.block_hash = genesis_block.calculate_block_hash()
        self.blocks.append(genesis_block)
    
    def add_transaction(self, vm_id: int, task: Dict, vm_before: Dict, vm_after: Dict, 
                       score: float, status: str) -> str:
        """Add a new scheduling transaction to the ledger"""
        self.transaction_counter += 1
        transaction_id = f"tx_{self.transaction_counter}_{int(time.time() * 1000)}"
        
        transaction = SchedulingTransaction(
            transaction_id=transaction_id,
            timestamp=time.time(),
            vm_id=vm_id,
            task_id=task['id'],
            task_requirements={
                'cpu': task['cpu'],
                'mem': task['mem'], 
                'io': task['io'],
                'bw': task['bw']
            },
            vm_state_before=vm_before.copy(),
            vm_state_after=vm_after.copy(),
            score=score,
            status=status
        )
        
        self.pending_transactions.append(transaction)
        
        # Create new block if we have enough transactions
        if len(self.pending_transactions) >= self.block_size:
            self._mine_block()
        
        return transaction_id
    
    def _mine_block(self):
        """Create a new block with pending transactions"""
        if not self.pending_transactions:
            return
        
        previous_hash = self.blocks[-1].block_hash if self.blocks else "0" * 64
        
        new_block = LedgerBlock(
            block_id=len(self.blocks),
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=previous_hash,
            merkle_root=""
        )
        
        # Calculate merkle root and block hash
        new_block.merkle_root = new_block.calculate_merkle_root()
        new_block.block_hash = new_block.calculate_block_hash()
        
        # Update transaction hashes
        for tx in new_block.transactions:
            tx.block_hash = new_block.block_hash
        
        self.blocks.append(new_block)
        self.pending_transactions.clear()
    
    def force_mine_block(self):
        """Force mining of current pending transactions (for testing/demo)"""
        if self.pending_transactions:
            self._mine_block()
    
    def get_transaction_history(self, vm_id: Optional[int] = None, 
                              task_id: Optional[str] = None) -> List[SchedulingTransaction]:
        """Get transaction history, optionally filtered by VM or task"""
        all_transactions = []
        
        # Get transactions from all blocks
        for block in self.blocks:
            all_transactions.extend(block.transactions)
        
        # Add pending transactions
        all_transactions.extend(self.pending_transactions)
        
        # Apply filters
        if vm_id is not None:
            all_transactions = [tx for tx in all_transactions if tx.vm_id == vm_id]
        
        if task_id is not None:
            all_transactions = [tx for tx in all_transactions if tx.task_id == task_id]
        
        return sorted(all_transactions, key=lambda x: x.timestamp)
    
    def get_vm_assignment_stats(self, vm_id: int) -> Dict:
        """Get assignment statistics for a specific VM"""
        vm_transactions = self.get_transaction_history(vm_id=vm_id)
        
        total_assignments = len([tx for tx in vm_transactions if tx.status == 'assigned'])
        failed_assignments = len([tx for tx in vm_transactions if tx.status == 'failed'])
        
        if vm_transactions:
            avg_score = sum(tx.score for tx in vm_transactions if tx.status == 'assigned') / max(total_assignments, 1)
            total_cpu_allocated = sum(tx.task_requirements['cpu'] for tx in vm_transactions if tx.status == 'assigned')
            total_mem_allocated = sum(tx.task_requirements['mem'] for tx in vm_transactions if tx.status == 'assigned')
        else:
            avg_score = 0
            total_cpu_allocated = 0
            total_mem_allocated = 0
        
        return {
            'vm_id': vm_id,
            'total_assignments': total_assignments,
            'failed_assignments': failed_assignments,
            'success_rate': total_assignments / max(total_assignments + failed_assignments, 1),
            'average_score': avg_score,
            'total_cpu_allocated': total_cpu_allocated,
            'total_mem_allocated': total_mem_allocated,
            'total_transactions': len(vm_transactions)
        }
    
    def validate_chain_integrity(self) -> bool:
        """Validate the integrity of the blockchain"""
        if not self.blocks:
            return True
        
        # Check genesis block
        if self.blocks[0].previous_hash != "0" * 64:
            return False
        
        # Check each block's hash and previous hash
        for i in range(1, len(self.blocks)):
            current_block = self.blocks[i]
            previous_block = self.blocks[i - 1]
            
            # Verify previous hash
            if current_block.previous_hash != previous_block.block_hash:
                return False
            
            # Verify block hash
            if current_block.block_hash != current_block.calculate_block_hash():
                return False
            
            # Verify merkle root
            if current_block.merkle_root != current_block.calculate_merkle_root():
                return False
        
        return True
    
    def get_ledger_summary(self) -> Dict:
        """Get summary statistics of the entire ledger"""
        total_blocks = len(self.blocks)
        total_transactions = sum(len(block.transactions) for block in self.blocks) + len(self.pending_transactions)
        
        all_transactions = []
        for block in self.blocks:
            all_transactions.extend(block.transactions)
        all_transactions.extend(self.pending_transactions)
        
        successful_assignments = len([tx for tx in all_transactions if tx.status == 'assigned'])
        failed_assignments = len([tx for tx in all_transactions if tx.status == 'failed'])
        
        return {
            'total_blocks': total_blocks,
            'total_transactions': total_transactions,
            'pending_transactions': len(self.pending_transactions),
            'successful_assignments': successful_assignments,
            'failed_assignments': failed_assignments,
            'success_rate': successful_assignments / max(total_transactions, 1),
            'chain_integrity': self.validate_chain_integrity(),
            'latest_block_hash': self.blocks[-1].block_hash if self.blocks else None
        }

# Singleton schedulers store
_scheduler_instances = {}

class BlockchainInspiredScheduler(Scheduler):
    def __init__(self, vm_capacity: Dict[str, int], alpha: float = 0.7, beta: float = 0.3, history_window: int = 10):
        super().__init__(vm_capacity)
        self.alpha = alpha
        self.beta = beta
        self.history_window = history_window
        self.resource_history = {}  # vm_id -> deque of usage records
        self.transaction_log = []  # Keep for backward compatibility
        self.ledger = DistributedTransactionLedger(block_size=5)  # Create distributed ledger
        print(f"BlockchainInspiredScheduler created: {id(self)} with distributed transaction ledger")

    def update_vm_history(self, vm):
        usage = {
            'cpu': vm.cpu / self.vm_capacity['cpu'],
            'mem': vm.mem / self.vm_capacity['mem'],
            'io': vm.io / self.vm_capacity['io'],
            'bw': vm.bw / self.vm_capacity['bw']
        }
        if vm.id not in self.resource_history:
            self.resource_history[vm.id] = deque(maxlen=self.history_window)
        self.resource_history[vm.id].append(usage)

    def calculate_cru(self, vm):
        # Current Resource Usage CRU (normalized utilizations)
        return (
            vm.cpu / self.vm_capacity['cpu'] +
            vm.mem / self.vm_capacity['mem'] +
            vm.io / self.vm_capacity['io'] +
            vm.bw / self.vm_capacity['bw']
        ) / 4

    def calculate_hru(self, vm):
        # Historical Resource Usage HRU
        history = self.resource_history.get(vm.id, [])
        if not history:
            return 0.0
        total = 0
        for entry in history:
            total += (entry['cpu'] + entry['mem'] + entry['io'] + entry['bw']) / 4
        return total / len(history)

    def calculate_dynamic_weight(self, vm):
        cru = self.calculate_cru(vm)
        hru = self.calculate_hru(vm)
        dw = self.alpha * cru + self.beta * hru
        return max(dw, 1e-6)  # Prevent zero-division

    def predict_vm_utilization(self, vm, task):
        # Predict utilization after assigning the task
        cpu_util = (vm.cpu + task['cpu']) / self.vm_capacity['cpu']
        mem_util = (vm.mem + task['mem']) / self.vm_capacity['mem']
        io_util  = (vm.io  + task['io'] ) / self.vm_capacity['io']
        bw_util  = (vm.bw  + task['bw'] ) / self.vm_capacity['bw']
        return cpu_util, mem_util, io_util, bw_util

    def vm_can_handle_task(self, vm, task):
        cpu_util, mem_util, io_util, bw_util = self.predict_vm_utilization(vm, task)
        return all(util <= 1.0 for util in [cpu_util, mem_util, io_util, bw_util])

    def calculate_urgency_factor(self, task, now=None):
        if now is None:
            now = time.time()
        deadline = task.get('deadline', now + 3600)
        tau = 1.0
        time_left = max(deadline - now, 1e-6)
        return 1.0 / (tau * time_left)

    def calculate_score(self, vm, task, now=None):
        uf = self.calculate_urgency_factor(task, now)
        dw = self.calculate_dynamic_weight(vm)
        return uf / dw

    def record_transaction(self, vm, task, score, status, vm_state_before=None):
        # Keep old transaction log for backward compatibility
        self.transaction_log.append({
            'timestamp': time.time(),
            'vm_id': vm.id,
            'task_id': task['id'],
            'score': score,
            'status': status
        })
        
        # Record in distributed ledger with detailed state information
        if vm_state_before is None:
            # Calculate state before assignment (current state minus task if assigned)
            vm_state_before = {
                'cpu': vm.cpu - (task['cpu'] if status == 'assigned' else 0),
                'mem': vm.mem - (task['mem'] if status == 'assigned' else 0),
                'io': vm.io - (task['io'] if status == 'assigned' else 0),
                'bw': vm.bw - (task['bw'] if status == 'assigned' else 0)
            }
        
        vm_state_after = {
            'cpu': vm.cpu,
            'mem': vm.mem,
            'io': vm.io,
            'bw': vm.bw
        }
        
        transaction_id = self.ledger.add_transaction(
            vm_id=vm.id,
            task=task,
            vm_before=vm_state_before,
            vm_after=vm_state_after,
            score=score,
            status=status
        )
        
        return transaction_id

    def schedule(self, task: Dict, vms: List) -> Tuple[Optional[VM], float]:
        now = time.time()
        for vm in vms:
            self.update_vm_history(vm)

        heap = []
        for vm in vms:
            if self.vm_can_handle_task(vm, task):
                score = self.calculate_score(vm, task, now)
                # Use negative score for max-heap
                heapq.heappush(heap, (-score, vm.id, vm))

        if heap:
            neg_score, _, best_vm = heapq.heappop(heap)
            final_score = -neg_score
            
            # Capture VM state before assignment
            vm_state_before = {
                'cpu': best_vm.cpu,
                'mem': best_vm.mem,
                'io': best_vm.io,
                'bw': best_vm.bw
            }
            
            self.record_transaction(best_vm, task, final_score, 'assigned', vm_state_before)
            return best_vm, final_score

        if vms:
            # For failed assignments, use the first VM as reference
            vm_state_before = {
                'cpu': vms[0].cpu,
                'mem': vms[0].mem,
                'io': vms[0].io,
                'bw': vms[0].bw
            }
            self.record_transaction(vms[0], task, 0, 'failed', vm_state_before)
        return None, float('inf')
    
    def get_ledger_stats(self) -> Dict:
        """Get comprehensive statistics from the distributed transaction ledger"""
        return self.ledger.get_ledger_summary()
    
    def get_vm_ledger_history(self, vm_id: int) -> Dict:
        """Get detailed assignment history for a specific VM from the ledger"""
        return self.ledger.get_vm_assignment_stats(vm_id)
    
    def get_task_ledger_history(self, task_id: str) -> List[SchedulingTransaction]:
        """Get all transactions related to a specific task"""
        return self.ledger.get_transaction_history(task_id=task_id)
    
    def validate_ledger_integrity(self) -> bool:
        """Validate the integrity of the distributed transaction ledger"""
        return self.ledger.validate_chain_integrity()
    
    def force_mine_pending_transactions(self):
        """Force mining of pending transactions (useful for testing/demos)"""
        self.ledger.force_mine_block()
    
    def get_recent_transactions(self, limit: int = 10) -> List[SchedulingTransaction]:
        """Get the most recent transactions from the ledger"""
        all_transactions = self.ledger.get_transaction_history()
        return all_transactions[-limit:] if all_transactions else []
    
    def export_ledger_data(self) -> Dict:
        """Export complete ledger data for analysis or backup"""
        return {
            'blocks': [
                {
                    'block_id': block.block_id,
                    'timestamp': block.timestamp,
                    'previous_hash': block.previous_hash,
                    'block_hash': block.block_hash,
                    'merkle_root': block.merkle_root,
                    'transactions': [tx.to_dict() for tx in block.transactions]
                }
                for block in self.ledger.blocks
            ],
            'pending_transactions': [tx.to_dict() for tx in self.ledger.pending_transactions],
            'summary': self.get_ledger_stats()
        }


# Factory to get the appropriate scheduler with singleton pattern
def get_scheduler(scheduler_type: str, vm_capacity: Dict[str, int]) -> Scheduler:
    global _scheduler_instances
    
    if scheduler_type not in _scheduler_instances:
        schedulers = {
            'roundrobin': RoundRobinScheduler,
            'urgency': UrgencyAwareScheduler,
            'leastloaded': LeastLoadedScheduler,
            'blockchain': BlockchainInspiredScheduler
        }
        _scheduler_instances[scheduler_type] = schedulers[scheduler_type](vm_capacity)
        if scheduler_type == 'blockchain':
            print(f"BlockchainInspiredScheduler created: {id(_scheduler_instances[scheduler_type])}")
    
    return _scheduler_instances[scheduler_type]
