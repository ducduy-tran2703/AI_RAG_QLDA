from fastapi import WebSocket
from typing import Dict, Set
import json

class ConnectionManager:
    def __init__(self):
        # Connections by check_id
        self.check_connections: Dict[str, Set[WebSocket]] = {}
        # Connections by user_id
        self.user_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, identifier: str, is_user: bool = False):
        await websocket.accept()
        target_dict = self.user_connections if is_user else self.check_connections
        if identifier not in target_dict:
            target_dict[identifier] = set()
        target_dict[identifier].add(websocket)

    def disconnect(self, websocket: WebSocket, identifier: str, is_user: bool = False):
        target_dict = self.user_connections if is_user else self.check_connections
        if identifier in target_dict:
            target_dict[identifier].discard(websocket)
            if not target_dict[identifier]:
                del target_dict[identifier]

    async def send_progress(self, check_id: str, data: dict):
        if check_id in self.check_connections:
            message = json.dumps(data)
            for ws in self.check_connections[check_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass

    async def broadcast_to_user(self, user_id: str, data: dict):
        if user_id in self.user_connections:
            message = json.dumps(data)
            for ws in self.user_connections[user_id]:
                try:
                    await ws.send_text(message)
                except Exception:
                    pass

manager = ConnectionManager()
