import subprocess
import tempfile
import os


WAV_TYPES = {"audio/wav", "audio/x-wav", "audio/wave"}


def convert_to_mp3(audio_bytes: bytes, content_type: str) -> tuple[bytes, str]:
    """
    If audio is WAV, convert to MP3 at 128 kbps using ffmpeg.
    Returns (bytes, content_type) — either converted or original unchanged.
    """
    if content_type not in WAV_TYPES:
        return audio_bytes, content_type

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as src:
        src.write(audio_bytes)
        src_path = src.name

    dst_path = src_path.replace(".wav", ".mp3")

    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", src_path,
                "-codec:a", "libmp3lame",
                "-b:a", "128k",
                "-ar", "44100",
                dst_path,
            ],
            check=True,
            capture_output=True,
        )
        with open(dst_path, "rb") as f:
            mp3_bytes = f.read()
        return mp3_bytes, "audio/mpeg"
    finally:
        os.unlink(src_path)
        if os.path.exists(dst_path):
            os.unlink(dst_path)
