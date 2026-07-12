"""Shared job store for real-time progress tracking."""

import threading

# Shared job storage
_jobs = {}  # job_id -> {"status": "running"|"completed"|"failed", "result": ..., "error": ..., "step_logs": [], "progress": {}}
_jobs_lock = threading.Lock()
