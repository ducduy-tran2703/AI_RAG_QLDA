import asyncio
import websockets
import sys

async def test_ws(check_id):
    uri = f"ws://localhost:8000/ws/{check_id}"
    async with websockets.connect(uri) as ws:
        print(f"Đã kết nối WebSocket, chờ tiến trình...")
        while True:
            msg = await ws.recv()
            print(msg)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Dùng: python test_ws.py <check_id>")
        sys.exit(1)
    check_id = sys.argv[1]
    asyncio.run(test_ws(check_id))