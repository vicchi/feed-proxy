"""
Feed Proxy API: gunicorn config settings
"""

daemon = False
pidfile = 'run/api.pid'
umask = 0o644
worker_tmp_dir = '/dev/shm'

workers = 1
max_requests = 10000
worker_class = 'uvicorn.workers.UvicornWorker'
