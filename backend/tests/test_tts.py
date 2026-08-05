import os
from pathlib import Path

from dotenv import load_dotenv

# Search for .env in current directory or project root
root_env = Path(__file__).resolve().parent.parent.parent / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()

try:
    import httpx
except ImportError:
    raise RuntimeError("Install backend/requirements.txt before running tests.")

import pytest


def test_tts():
    if os.getenv("RUN_LIVE_SAHARA_TESTS") != "1":
        pytest.skip("Set RUN_LIVE_SAHARA_TESTS=1 to exercise the paid Sahara TTS API.")

    api_key = os.getenv("SAHARA_API_KEY")
    if not api_key:
        raise RuntimeError("SAHARA_API_KEY is required for the live TTS test.")

    url = "https://infer.voice.intron.io/tts/v1/generate"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "text": "Hello world, this is a test of Intron TTS.",
        "voice": "en-US-Neural2-F",
        "audio_config": {"audio_encoding": "MP3"},
    }

    print(f"[+] Sending TTS request to {url}...")
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        pytest.fail(f"Sahara TTS request failed: {exc}")

    output_dir = Path(__file__).resolve().parent
    output_file = output_dir / "test_tts.mp3"
    output_file.write_bytes(response.content)
    assert response.content
    print(f"[+] Success! Audio saved to {output_file} ({len(response.content)} bytes)")


if __name__ == "__main__":
    test_tts()
