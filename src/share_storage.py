import base64
import os
import secrets
from datetime import datetime, timedelta, timezone

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except ImportError:
    boto3 = None
    BotoCoreError = Exception
    ClientError = Exception


GENERATED_PREFIX = "generated"


def utc_now():
    return datetime.now(timezone.utc)


def create_share_id(ttl_hours):
    expires_at = utc_now() + timedelta(hours=ttl_hours)
    token = secrets.token_urlsafe(10)
    return f"{int(expires_at.timestamp())}-{token}", expires_at


def parse_share_expiry(share_id):
    try:
        expires_epoch = int(share_id.split("-", 1)[0])
        return datetime.fromtimestamp(expires_epoch, timezone.utc)
    except (TypeError, ValueError, IndexError, OSError):
        return None


def is_share_expired(share_id):
    expires_at = parse_share_expiry(share_id)
    return expires_at is None or utc_now() > expires_at


def encode_metadata_text(value):
    if not value:
        return ""
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii")


def decode_metadata_text(value):
    if not value:
        return ""
    try:
        return base64.urlsafe_b64decode(value.encode("ascii")).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return ""


class ShareStorage:
    def __init__(self, client, bucket):
        self.client = client
        self.bucket = bucket

    @classmethod
    def from_env(cls):
        bucket = os.environ.get("R2_BUCKET")
        access_key = os.environ.get("R2_ACCESS_KEY_ID")
        secret_key = os.environ.get("R2_SECRET_ACCESS_KEY")
        endpoint_url = os.environ.get("R2_ENDPOINT_URL")
        account_id = os.environ.get("R2_ACCOUNT_ID")

        if not endpoint_url and account_id:
            endpoint_url = f"https://{account_id}.r2.cloudflarestorage.com"

        if not all([bucket, access_key, secret_key, endpoint_url]):
            return None

        if boto3 is None:
            print("[Warning] R2 sharing is configured, but boto3 is not installed")
            return None

        client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="auto",
        )
        return cls(client=client, bucket=bucket)

    def object_key(self, share_id):
        return f"{GENERATED_PREFIX}/{share_id}.mp3"

    def upload_audio(self, share_id, audio_bytes, expires_at, custom_name):
        self.client.put_object(
            Bucket=self.bucket,
            Key=self.object_key(share_id),
            Body=audio_bytes,
            ContentType="audio/mpeg",
            CacheControl="private, max-age=86400",
            Metadata={
                "expires_at": expires_at.isoformat(),
            },
        )

    def get_audio(self, share_id):
        try:
            return self.client.get_object(
                Bucket=self.bucket,
                Key=self.object_key(share_id),
            )
        except (BotoCoreError, ClientError) as exc:
            raise FileNotFoundError(str(exc)) from exc

    def video_object_key(self, share_id):
        return f"{GENERATED_PREFIX}/video/{share_id}.mp4"

    def upload_video(self, share_id, video_bytes, expires_at, custom_name):
        self.client.put_object(
            Bucket=self.bucket,
            Key=self.video_object_key(share_id),
            Body=video_bytes,
            ContentType="video/mp4",
            CacheControl="private, max-age=86400",
            Metadata={
                "expires_at": expires_at.isoformat(),
                "custom_name_b64": encode_metadata_text(custom_name),
            },
        )

    def get_video_metadata(self, share_id):
        try:
            response = self.client.head_object(
                Bucket=self.bucket,
                Key=self.video_object_key(share_id),
            )
            return response.get("Metadata", {})
        except (BotoCoreError, ClientError) as exc:
            raise FileNotFoundError(str(exc)) from exc

    def get_custom_name(self, metadata):
        return decode_metadata_text(metadata.get("custom_name_b64"))

    def get_video(self, share_id):
        try:
            return self.client.get_object(
                Bucket=self.bucket,
                Key=self.video_object_key(share_id),
            )
        except (BotoCoreError, ClientError) as exc:
            raise FileNotFoundError(str(exc)) from exc
