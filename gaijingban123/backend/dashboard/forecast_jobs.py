import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path

from django.conf import settings


# In-memory job registry
_jobs = {}
_lock = threading.Lock()


def create_job():
    """Create a new forecast job and return its ID."""
    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {
            "id": job_id,
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "started_at": None,
            "finished_at": None,
            "return_code": None,
            "error_message": None,
        }
    return job_id


def get_job(job_id):
    """Get job status by ID."""
    with _lock:
        return _jobs.get(job_id)


def list_jobs():
    """List all jobs."""
    with _lock:
        return list(_jobs.values())


def is_any_job_running():
    """Check if any job is currently running."""
    with _lock:
        return any(job["status"] == "running" for job in _jobs.values())


def run_forecast_script(job_id):
    """Run the monthly_sales_forecast.py script in a background thread."""
    script_path = Path(settings.PROJECT_ROOT) / "monthly_sales_forecast.py"

    if not script_path.exists():
        with _lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["finished_at"] = datetime.now().isoformat()
                _jobs[job_id]["error_message"] = f"Script not found: {script_path}"
        return

    # Update status to running
    with _lock:
        if job_id in _jobs:
            _jobs[job_id]["status"] = "running"
            _jobs[job_id]["started_at"] = datetime.now().isoformat()

    try:
        # Run the script in the project root directory
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(settings.PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=600,  # 10 minute timeout
        )

        with _lock:
            if job_id in _jobs:
                _jobs[job_id]["return_code"] = result.returncode
                _jobs[job_id]["finished_at"] = datetime.now().isoformat()

                if result.returncode == 0:
                    _jobs[job_id]["status"] = "succeeded"
                else:
                    _jobs[job_id]["status"] = "failed"
                    _jobs[job_id]["error_message"] = (
                        f"Script exited with code {result.returncode}. "
                        f"stderr: {result.stderr[-500:]}"  # Last 500 chars
                    )

    except subprocess.TimeoutExpired:
        with _lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["finished_at"] = datetime.now().isoformat()
                _jobs[job_id]["error_message"] = "Script execution timeout (10 minutes)"

    except Exception as exc:
        with _lock:
            if job_id in _jobs:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["finished_at"] = datetime.now().isoformat()
                _jobs[job_id]["error_message"] = str(exc)


def start_job(job_id):
    """Start running a forecast job in a background thread."""
    thread = threading.Thread(target=run_forecast_script, args=(job_id,), daemon=True)
    thread.start()
