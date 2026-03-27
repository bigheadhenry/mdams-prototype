import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://meam:meam_secret@db:5432/meam_db")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
API_PUBLIC_URL = os.getenv("API_PUBLIC_URL", "http://localhost:3000/api")
CANTALOUPE_PUBLIC_URL = os.getenv("CANTALOUPE_PUBLIC_URL", "http://localhost:3000/iiif/2")
