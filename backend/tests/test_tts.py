import os
import sys
import json
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
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "httpx"])
    import httpx

def test_tts():
    api_key = os.getenv("SAHARA_API_KEY")
    if not api_key:
        print("[-] SAHARA_API_KEY environment variable is not set!")
        print("    Please set it in PowerShell with: $env:SAHARA_API_KEY='your_key'")
        return

    url = "https://infer.voice.intron.io/tts/v1/generate"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "text": "Hello world, this is a test of Intron TTS.",
        "voice": "en-US-Neural2-F",
        "audio_config": {
            "audio_encoding": "MP3"
        }
    }

    print(f"[+] Sending TTS request to {url}...")
    try:
        response = httpx.post(url, headers=headers, json=payload, timeout=30.0)
        print(f"[+] Status Code: {response.status_code}")
        if response.status_code == 200:
            output_dir = Path(__file__).resolve().parent
            output_file = output_dir / "test_tts.mp3"
            with open(output_file, "wb") as f:
                f.write(response.content)
            print(f"[+] Success! Audio saved to {output_file} ({len(response.content)} bytes)")
        else:
            print(f"[-] Error response:\n{response.text}")
    except Exception as e:
        print(f"[-] HTTP Error: {e}")

if __name__ == "__main__":
    test_tts()
