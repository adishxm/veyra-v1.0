import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class JobRecord:
    job_id: str
    status: str  # "PENDING", "PROCESSING", "COMPLETED", "FAILED"
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_items: int = 0
    completed_items: int = 0
    results: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None


class JobManager:
    """In-memory asynchronous background task runner and status tracker."""

    def __init__(self):
        self._jobs: Dict[str, JobRecord] = {}

    def create_job(self, total_items: int) -> JobRecord:
        job_id = str(uuid.uuid4())[:8]
        record = JobRecord(
            job_id=job_id,
            status="PENDING",
            created_at=datetime.now(timezone.utc),
            total_items=total_items,
        )
        self._jobs[job_id] = record
        return record

    def get_job(self, job_id: str) -> Optional[JobRecord]:
        return self._jobs.get(job_id)

    def update_progress(self, job_id: str, results: List[Dict[str, Any]]) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].status = "COMPLETED"
            self._jobs[job_id].completed_at = datetime.now(timezone.utc)
            self._jobs[job_id].completed_items = len(results)
            self._jobs[job_id].results = results

    def fail_job(self, job_id: str, error: str) -> None:
        if job_id in self._jobs:
            self._jobs[job_id].status = "FAILED"
            self._jobs[job_id].completed_at = datetime.now(timezone.utc)
            self._jobs[job_id].error = error


job_manager = JobManager()