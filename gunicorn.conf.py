# pylint: disable=invalid-name
"""
Feed Proxy API: gunicorn config settings
"""

import multiprocessing

# Server Mechanics: https://docs.gunicorn.org/en/latest/settings.html#server-mechanics
daemon = False
pidfile = 'run/api.pid'
umask = 0o644
worker_tmp_dir = '/dev/shm'
forwarded_allow_ips = '*'

# Worker Processes: https://docs.gunicorn.org/en/latest/settings.html#worker-processes
workers = multiprocessing.cpu_count() * 2 + 1
max_requests = 10000
worker_class = 'uvicorn.workers.UvicornWorker'

# Logging: https://docs.gunicorn.org/en/stable/settings.html#logging
# accesslog = '-'
errorlog = '-'
loglevel = 'info'
