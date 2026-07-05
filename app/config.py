import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]
AWS_REGION = os.environ.get("AWS_REGION", "ap-south-1")
S3_BUCKET_NAME = os.environ["S3_BUCKET_NAME"]
CLOUDFRONT_DOMAIN = os.environ["CLOUDFRONT_DOMAIN"]
CLOUDFRONT_KEY_PAIR_ID = os.environ["CLOUDFRONT_KEY_PAIR_ID"]
CLOUDFRONT_PRIVATE_KEY_PATH = os.environ["CLOUDFRONT_PRIVATE_KEY_PATH"]

APP_SECRET_KEY = os.environ["APP_SECRET_KEY"]
APP_BASE_URL = os.environ.get("APP_BASE_URL", "http://localhost:8000")
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")

MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB
ALLOWED_AUDIO_TYPES = {"audio/mpeg", "audio/mp4", "audio/aac", "audio/x-m4a"}
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
SIGNED_URL_EXPIRY_SECONDS = 4 * 3600  # 4 hours
