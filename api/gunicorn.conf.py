# gunicorn.conf.py
# Production configuration for api-diet FastAPI with Uvicorn workers

import multiprocessing
import os

# Server socket
bind = os.getenv("BIND", "0.0.0.0:8000")

# Worker processes
# Formula: (2 x CPU cores) + 1 for I/O bound applications
# For Fly.io: use environment variable to control, default to auto-calculation
workers = int(os.getenv("UVICORN_WORKERS", (2 * multiprocessing.cpu_count()) + 1))

# Use Uvicorn's worker class for async support
worker_class = "uvicorn.workers.UvicornWorker"

# Worker connections (per worker)
worker_connections = 1000

# Timeout configuration
timeout = 120  # Request timeout in seconds
graceful_timeout = 30  # Graceful shutdown timeout
keepalive = 5  # Keep-alive connections timeout

# Worker recycling to prevent memory leaks
max_requests = 10000  # Restart worker after this many requests
max_requests_jitter = 1000  # Randomize restart to avoid thundering herd

# Logging
loglevel = os.getenv("LOG_LEVEL", "info")
accesslog = "-"  # stdout
errorlog = "-"  # stderr
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "api-diet"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (handled by Fly.io, so disabled here)
keyfile = None
certfile = None

# Preload app DISABLED to prevent segfaults with native extensions (BAML Rust, greenlet, psycopg2)
# When preload_app=True, native extensions initialized in master become corrupted after fork
# See: https://github.com/benoitc/gunicorn/issues/2478
preload_app = False

# Forward proxy headers (important for Fly.io)
forwarded_allow_ips = "*"
proxy_allow_ips = "*"

# Hooks for logging (uncomment and customize as needed)
# def on_starting(server):
#     """Called just before the master process is initialized."""
#     pass
#
# def on_reload(server):
#     """Called to recycle workers during a reload via SIGHUP."""
#     pass
#
# def worker_int(worker):
#     """Called when a worker receives SIGINT or SIGQUIT."""
#     pass
#
# def worker_abort(worker):
#     """Called when a worker receives SIGABRT."""
#     pass
