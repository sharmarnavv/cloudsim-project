# Appendix: Core Implementation Code

## A.1 Distributed Transaction Ledger

### A.1.1 Transaction and Block Structure
```python
from dataclasses import dataclass
import hashlib
import json
import time

@dataclass
class SchedulingTransaction:
    transaction_id: str
    timestamp: float
    vm_id: int
    task_id: str
    task_requirements: Dict[str, int]
    vm_state_before: Dict[str, int]
    vm_state_after: Dict[str, int]
    score: float
    status: str  # 'assigned', 'failed'
    block_hash: str = ""

@dataclass
class LedgerBlock:
    block_id: int
    timestamp: float
    transactions: List[SchedulingTransaction]
    previous_hash: str
    merkle_root: str
    block_hash: str = ""
    
    def calculate_merkle_root(self) -> str:
        """Calculate merkle root using binary tree construction"""
        if not self.transactions:
            return hashlib.sha256("empty_block".encode()).hexdigest()
        
        tx_hashes = [self._hash_transaction(tx) for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])
            
            new_level = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                new_level.append(hashlib.sha256(combined.encode()).hexdigest())
            tx_hashes = new_level
        
        return tx_hashes[0]
    
    def _hash_transaction(self, tx: SchedulingTransaction) -> str:
        tx_dict = tx.to_dict()
        tx_dict.pop('block_hash', None)  # Prevent circular dependency
        tx_data = json.dumps(tx_dict, sort_keys=True)
        return hashlib.sha256(tx_data.encode()).hexdigest()
```

### A.1.2 Ledger Core Logic
```python
class DistributedTransactionLedger:
    def __init__(self, block_size: int = 10):
        self.blocks: List[LedgerBlock] = []
        self.pending_transactions: List[SchedulingTransaction] = []
        self.block_size = block_size
        self._create_genesis_block()
    
    def add_transaction(self, vm_id: int, task: Dict, vm_before: Dict, 
                       vm_after: Dict, score: float, status: str) -> str:
        transaction = SchedulingTransaction(
            transaction_id=f"tx_{int(time.time() * 1000)}",
            timestamp=time.time(),
            vm_id=vm_id,
            task_id=task['id'],
            task_requirements={'cpu': task['cpu'], 'mem': task['mem'], 
                             'io': task['io'], 'bw': task['bw']},
            vm_state_before=vm_before.copy(),
            vm_state_after=vm_after.copy(),
            score=score,
            status=status
        )
        
        self.pending_transactions.append(transaction)
        
        if len(self.pending_transactions) >= self.block_size:
            self._mine_block()
        
        return transaction.transaction_id
    
    def _mine_block(self):
        """Create new block with cryptographic validation"""
        previous_hash = self.blocks[-1].block_hash if self.blocks else "0" * 64
        
        new_block = LedgerBlock(
            block_id=len(self.blocks),
            timestamp=time.time(),
            transactions=self.pending_transactions.copy(),
            previous_hash=previous_hash,
            merkle_root=""
        )
        
        new_block.merkle_root = new_block.calculate_merkle_root()
        new_block.block_hash = new_block.calculate_block_hash()
        
        self.blocks.append(new_block)
        self.pending_transactions.clear()
```

## A.2 Blockchain-Inspired Scheduling Algorithm

### A.2.1 Dynamic Weight and Scoring
```python
def calculate_dynamic_weight(self, vm):
    """DW = α × Current_Usage + β × Historical_Usage"""
    cru = (vm.cpu/self.vm_capacity['cpu'] + vm.mem/self.vm_capacity['mem'] + 
           vm.io/self.vm_capacity['io'] + vm.bw/self.vm_capacity['bw']) / 4
    
    history = self.resource_history.get(vm.id, [])
    hru = sum((h['cpu'] + h['mem'] + h['io'] + h['bw'])/4 for h in history) / max(len(history), 1)
    
    return max(self.alpha * cru + self.beta * hru, 1e-6)

def calculate_urgency_factor(self, task, now=None):
    """UF = 1 / (τ × time_remaining)"""
    if now is None:
        now = time.time()
    time_left = max(task.get('deadline', now + 3600) - now, 1e-6)
    return 1.0 / time_left

def schedule(self, task: Dict, vms: List) -> Tuple[Optional[VM], float]:
    """Main scheduling: Score = UF / DW (higher is better)"""
    now = time.time()
    
    heap = []
    for vm in vms:
        if self.vm_can_handle_task(vm, task):
            uf = self.calculate_urgency_factor(task, now)
            dw = self.calculate_dynamic_weight(vm)
            score = uf / dw
            heapq.heappush(heap, (-score, vm.id, vm))

    if heap:
        neg_score, _, best_vm = heapq.heappop(heap)
        final_score = -neg_score
        
        vm_state_before = {'cpu': best_vm.cpu, 'mem': best_vm.mem, 
                          'io': best_vm.io, 'bw': best_vm.bw}
        self.record_transaction(best_vm, task, final_score, 'assigned', vm_state_before)
        return best_vm, final_score

    return None, float('inf')
```

## A.3 Cryptographic Validation

### A.3.1 Chain Integrity Validation
```python
def validate_chain_integrity(self) -> bool:
    """Multi-layer blockchain validation"""
    if not self.blocks:
        return True
    
    # Validate genesis block
    if self.blocks[0].previous_hash != "0" * 64:
        return False
    
    # Validate each subsequent block
    for i in range(1, len(self.blocks)):
        current_block = self.blocks[i]
        previous_block = self.blocks[i - 1]
        
        # Verify hash chain linking
        if current_block.previous_hash != previous_block.block_hash:
            return False
        
        # Verify block hash integrity
        if current_block.block_hash != current_block.calculate_block_hash():
            return False
        
        # Verify merkle root integrity
        if current_block.merkle_root != current_block.calculate_merkle_root():
            return False
    
    return True

def calculate_block_hash(self) -> str:
    """Generate SHA-256 hash of entire block"""
    block_data = {
        'block_id': self.block_id,
        'timestamp': self.timestamp,
        'previous_hash': self.previous_hash,
        'merkle_root': self.merkle_root,
        'transaction_count': len(self.transactions)
    }
    return hashlib.sha256(json.dumps(block_data, sort_keys=True).encode()).hexdigest()
```