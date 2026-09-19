import time
import httpx

PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6300010000000500010d0a2db40000000049454e44ae426082"
)

files = {"photo": ("test.png", PNG, "image/png")}
data = {
    "latitude": "12.9716",
    "longitude": "77.5946",
    "captured_at": "2026-09-16T12:00:00Z",
    "description": "smoke visible near MG Road",
}

t0 = time.time()
try:
    r = httpx.post(
        "http://127.0.0.1:8000/api/incidents/realtime",
        files=files, data=data, timeout=60,
    )
    print(f"elapsed: {time.time()-t0:.2f}s")
    print(r.status_code)
    print(r.json())
except Exception as e:
    print(f"elapsed: {time.time()-t0:.2f}s")
    print(f"error: {type(e).__name__}: {e}")