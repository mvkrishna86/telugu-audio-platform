import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "")
DATABASE_URL = os.environ["DATABASE_URL"]

AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
S3_BUCKET_NAME = os.environ.get("S3_BUCKET_NAME", "")
CLOUDFRONT_DOMAIN = os.environ.get("CLOUDFRONT_DOMAIN", "")
CLOUDFRONT_KEY_PAIR_ID = os.environ.get("CLOUDFRONT_KEY_PAIR_ID", "")
CLOUDFRONT_PRIVATE_KEY_PATH = os.environ.get("CLOUDFRONT_PRIVATE_KEY_PATH", "")

APP_SECRET_KEY = os.environ.get("APP_SECRET_KEY", "dev-secret-change-in-production")
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

MAX_UPLOAD_BYTES = 500 * 1024 * 1024
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/mp4", "audio/aac", "audio/x-m4a"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
SIGNED_URL_EXPIRY_SECONDS = 4 * 3600
