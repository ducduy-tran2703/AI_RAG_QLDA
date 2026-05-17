from fastapi import WebSocket
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        # Lưu các kết nối theo check_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, check_id: str):
        await websocket.accept()
        if check_id not in self.active_connections:
            self.active_connections[check_id] = set()
        self.active_connections[check_id].add(websocket)

    def disconnect(self, websocket: WebSocket, check_id: str):
        if check_id in self.active_connections:
            self.active_connections[check_id].discard(websocket)
            if not self.active_connections[check_id]:
                del self.active_connections[check_id]

    async def send_progress(self, check_id: str, data: dict):
        if check_id in self.active_connections:
            for ws in self.active_connections[check_id]:
                await ws.send_text(json.dumps(data))

manager = ConnectionManager()