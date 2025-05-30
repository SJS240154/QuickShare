# Gunicorn configuration file
import multiprocessing

# Server socket
bind = '127.0.0.1:8000'
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 2

# Process naming
proc_name = 'gunicorn_flask_file_transfer'

# Logging
accesslog = 'access.log'
errorlog = 'error.log'
loglevel = 'info'

# Server mechanics
daemon = False
pidfile = 'gunicorn.pid'
user = None
group = None
umask = 0
tmp_upload_dir = None

# Maximum size of HTTP request line in bytes
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Maximum number of requests a worker will process before restarting
max_requests = 2000
max_requests_jitter = 200

# Timeout for graceful workers restart
graceful_timeout = 30

# For debugging and testing
spew = False
check_config = False