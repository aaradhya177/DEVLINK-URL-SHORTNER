import os


os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://devlink:devlink@localhost:5432/devlink_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("KAFKA_BROKERS", "localhost:9092")
os.environ.setdefault("JWT_SECRET", "0123456789abcdef0123456789abcdef")
os.environ.setdefault("DEVLINK_WORKER_ID", "1")
