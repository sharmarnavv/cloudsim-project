from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from schedulers import get_scheduler, VM

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
VM_CAPACITY = {
    'cpu': 500,
    'mem': 250,
    'io': 300,
    'bw': 20
}

SCHEDULERS = {
    'roundrobin': get_scheduler('roundrobin', VM_CAPACITY),
    'urgency': get_scheduler('urgency', VM_CAPACITY),
    'leastloaded': get_scheduler('leastloaded', VM_CAPACITY),
    'blockchain': get_scheduler('blockchain', VM_CAPACITY)
}

class Task(BaseModel):
    id: int
    cpu: int
    mem: int
    io: int
    bw: int
    deadline: int
    duration: int

class ScheduleRequest(BaseModel):
    task: Task
    scheduler_type: str
    vm_states: List[Dict]

class ScheduleResponse(BaseModel):
    success: bool
    vm_id: Optional[int] = None
    score: Optional[float] = None
    message: Optional[str] = None

@app.post("/schedule", response_model=ScheduleResponse)
async def schedule_task(request: ScheduleRequest):
    try:
        print(f"Scheduling with {request.scheduler_type} scheduler")
        # Create scheduler
        scheduler = SCHEDULERS[request.scheduler_type]
        
        # Recreate VMs with their current state
        vms = []
        for state in request.vm_states:
            vm = VM(state['id'], VM_CAPACITY)
            vm.cpu = state['cpu']
            vm.mem = state['mem']
            vm.io = state['io']
            vm.bw = state['bw']
            vm.tasks = state['tasks']
            vms.append(vm)
        
        # Schedule the task
        selected_vm, score = scheduler.schedule(request.task.dict(), vms)
        
        if selected_vm:
            return ScheduleResponse(
                success=True,
                vm_id=selected_vm.id,
                score=score
            )
        else:
            return ScheduleResponse(
                success=False,
                message="No suitable VM found"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/config")
async def get_config():
    return {"vm_capacity": VM_CAPACITY}

@app.get("/ledger/{scheduler_type}")
async def get_ledger(scheduler_type: str):
    """Get blockchain ledger data for the specified scheduler"""
    try:
        if scheduler_type not in SCHEDULERS:
            raise HTTPException(status_code=404, detail="Scheduler not found")
        
        scheduler = SCHEDULERS[scheduler_type]
        
        # Check if this scheduler has ledger functionality
        if not hasattr(scheduler, 'get_ledger_stats'):
            raise HTTPException(status_code=400, detail="This scheduler does not support ledger functionality")
        
        # Get comprehensive ledger data
        ledger_data = {
            'summary': scheduler.get_ledger_stats(),
            'recent_transactions': [tx.to_dict() for tx in scheduler.get_recent_transactions(20)],
            'vm_stats': {},
            'export_data': scheduler.export_ledger_data()
        }
        
        # Get VM-specific statistics
        # We need to determine which VMs exist based on recent transactions
        vm_ids = set()
        for tx in scheduler.get_recent_transactions(100):  # Look at more transactions to find all VMs
            vm_ids.add(tx.vm_id)
        
        for vm_id in vm_ids:
            ledger_data['vm_stats'][vm_id] = scheduler.get_vm_ledger_history(vm_id)
        
        return ledger_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
