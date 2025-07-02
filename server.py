import subprocess

# Start FastAPI server
uvicorn_proc = subprocess.Popen(["uvicorn", "main:app", "--reload"])

# Start Selenium worker
worker_proc = subprocess.Popen(["python", "selenium_worker.py"])

# Wait for both to finish (they won't, unless killed)
uvicorn_proc.wait()
worker_proc.wait()