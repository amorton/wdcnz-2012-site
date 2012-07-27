# Use redis as the message broker.
BROKER_URL = "redis://localhost:6379/0"

# This is the task status stored. 
# Want to change to cassandra later 

CELERY_RESULT_BACKEND = "redis"
CELERY_REDIS_HOST = "localhost"
CELERY_REDIS_PORT = 6379
CELERY_REDIS_DB = 0

CELERYD_LOG_FORMAT="%(asctime)s - %(processName)s - %(name)s - %(lineno)d - %(levelname)s - %(message)s"

# This tells the celery worker server to look in tasks.py for tasks
CELERY_IMPORTS = ("wdcnz.tasks", )