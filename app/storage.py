import uuid
import boto3
from botocore.signers import CloudFrontSigner
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
import datetime

from app.config import (
    AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION,
    S3_BUCKET_NAME, CLOUDFRONT_DOMAIN, CLOUDFRONT_KEY_PAIR_ID,
    CLOUDFRONT_PRIVATE_KEY_PATH, SIGNED_URL_EXPIRY_SECONDS,
)


def _s3_client():
    return boto3.client(
        "s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    )


def upload_file_to_s3(file_bytes: bytes, content_type: str, folder: str) -> str:
    """Upload bytes to S3 and return the object key."""
    key = f"{folder}/{uuid.uuid4()}"
    _s3_client().put_object(
        Bucket=S3_BUCKET_NAME,
        Key=key,
        Body=file_bytes,
        ContentType=content_type,
    )
    return key


def delete_s3_object(key: str) -> None:
    _s3_client().delete_object(Bucket=S3_BUCKET_NAME, Key=key)


def _rsa_signer(message: bytes) -> bytes:
    with open(CLOUDFRONT_PRIVATE_KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    return private_key.sign(message, padding.PKCS1v15(), hashes.SHA1())  # noqa: S303 – CloudFront requires SHA1


def get_signed_url(s3_key: str) -> str:
    """Return a CloudFront signed URL valid for SIGNED_URL_EXPIRY_SECONDS."""
    cf_signer = CloudFrontSigner(CLOUDFRONT_KEY_PAIR_ID, _rsa_signer)
    expire_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=SIGNED_URL_EXPIRY_SECONDS)
    url = f"{CLOUDFRONT_DOMAIN.rstrip('/')}/{s3_key}"
    return cf_signer.generate_presigned_url(url, date_less_than=expire_at)
