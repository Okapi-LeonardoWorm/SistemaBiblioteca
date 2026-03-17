from datetime import datetime
from threading import Lock
from uuid import uuid4


_jobs = {}
_jobs_lock = Lock()


def create_job(owner_user_id: int, kind: str, metadata: dict | None = None) -> str:
    job_id = str(uuid4())
    now = datetime.utcnow().isoformat()
    with _jobs_lock:
        _jobs[job_id] = {
            'jobId': job_id,
            'ownerUserId': owner_user_id,
            'kind': kind,
            'status': 'queued',
            'progress': 0,
            'createdAt': now,
            'updatedAt': now,
            'metadata': metadata or {},
            'summary': {
                'totalRows': 0,
                'processedRows': 0,
                'successRows': 0,
                'errorRows': 0,
            },
            'errorReportPath': None,
            'messages': [],
        }
    return job_id


def update_job(job_id: str, **fields):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        for key, value in fields.items():
            if key == 'summary' and isinstance(value, dict):
                job['summary'].update(value)
            else:
                job[key] = value
        job['updatedAt'] = datetime.utcnow().isoformat()
        return dict(job)


def add_job_message(job_id: str, message: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        job['messages'].append(message)
        job['updatedAt'] = datetime.utcnow().isoformat()
        return dict(job)


def get_job(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        return dict(job)
