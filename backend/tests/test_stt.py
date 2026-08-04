import asyncio
import base64
import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current directory or project root
root_env = Path(__file__).resolve().parent.parent.parent / ".env"
if root_env.exists():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets"])
    import websockets

async def test_stt():
    api_key = os.getenv("SAHARA_API_KEY")
    if not api_key:
        print("[-] SAHARA_API_KEY environment variable is not set!")
        print("    Please set it in PowerShell with: $env:SAHARA_API_KEY='your_key'")
        return

    url = "wss://infer.voice.intron.io/stt/v1/stream?sample_rate=16000&bit_rate=16&num_channels=1&use_language_asr_input=en"
    headers = {"Authorization": f"Bearer {api_key}"}

    print(f"[+] 1. Connecting to Intron STT WebSocket...")
    
    ws = None
    for param in ["additional_headers", "extra_headers", "headers"]:
        try:
            ws = await websockets.connect(url, **{param: headers})
            break
        except TypeError:
            continue

    if not ws:
        print("[-] Failed to initialize websocket connection.")
        return

    async with ws:
        # 1. Receive SESSION_CREATED
        first_msg = await ws.recv()
        session_data = json.loads(first_msg)
        print(f"[+] 2. Received Session Init:\n    {session_data}")
        
        if session_data.get("message_type") != "SESSION_CREATED":
            print(f"[-] Unexpected response: {first_msg}")
            return

        # 2. Send 1 second of 16kHz PCM16LE audio
        dummy_audio = b"\x00" * 32000 
        audio_b64 = base64.b64encode(dummy_audio).decode("utf-8")
        
        print("[+] 3. Sending INPUT_AUDIO_CHUNK...")
        chunk_msg = {
            "message_type": "INPUT_AUDIO_CHUNK",
            "audio_base_64": audio_b64,
            "ack_id": 1
        }
        await ws.send(json.dumps(chunk_msg))

        # 3. Send COMMIT
        print("[+] 4. Sending COMMIT...")
        commit_msg = {"message_type": "COMMIT"}
        await ws.send(json.dumps(commit_msg))

        # 4. Listen for server responses (ACK, PARTIAL_TRANSCRIPT, COMMITTED_TRANSCRIPT)
        print("[+] 5. Listening for transcription response from server...")
        try:
            while True:
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                resp_json = json.loads(response)
                msg_type = resp_json.get("message_type")
                print(f"    <- Received [{msg_type}]: {resp_json}")
                
                if msg_type in ("COMMITTED_TRANSCRIPT", "AUTHENTICATION_ERROR", "INSUFFICIENT_AUDIO_ACTIVITY"):
                    break
        except asyncio.TimeoutError:
            print("[+] Finished listening for responses.")

    print("[+] STT Phase 1 test complete!")

if __name__ == "__main__":
    asyncio.run(test_stt())
