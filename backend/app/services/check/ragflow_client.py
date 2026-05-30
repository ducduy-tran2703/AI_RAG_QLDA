"""
RAGFlow Client — Async client for RAGFlow Chat API
====================================================
Dùng trong pipeline backend để gửi chunk đến RAGFlow và nhận kết quả LLM.

Dựa trên code từ backend/source/send_to_ragflow.py (sync → async).
"""

import json
import re
import uuid
from typing import Optional

import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from ...shared.config import settings


# ══════════════════════════════════════════════════════════════════════
# CẤU HÌNH
# ══════════════════════════════════════════════════════════════════════

RAGFLOW_BASE_URL    = settings.ragflow_base_url.rstrip("/")
RAGFLOW_API_KEY     = settings.ragflow_api_key
# Dùng manifest assistant ID mặc định (kiểm tra thể thức)
ASSISTANT_ID        = settings.RAGFLOW_ASSISTANT_MANIFEST_ID

TIMEOUT_SECONDS     = 60
DELAY_BETWEEN_CHUNKS = 0.5


class RAGFlowError(Exception):
    """Lỗi từ RAGFlow API"""
    pass


class RAGFlowClient:
    """Async client giao tiếp với RAGFlow Chat API"""

    def __init__(self):
        self.base_url = RAGFLOW_BASE_URL
        self.api_key = RAGFLOW_API_KEY
        self.assistant_id = ASSISTANT_ID
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=aiohttp.ClientTimeout(total=TIMEOUT_SECONDS),
            )
        return self._session

    async def create_session(self) -> str:
        """
        Tạo session mới trên RAGFlow.
        Mỗi chunk dùng 1 session riêng để tránh context nhiễm.
        """
        url = f"{self.base_url}/api/v1/chats/{self.assistant_id}/sessions"
        payload = {"name": f"check_{uuid.uuid4().hex[:8]}"}

        session = await self._get_session()
        try:
            async with session.post(url, json=payload) as resp:
                data = await resp.json()
                if data.get("code") == 0:
                    return data["data"]["id"]
                raise RAGFlowError(f"Tạo session thất bại: {data.get('message')}")
        except aiohttp.ClientError as e:
            raise RAGFlowError(f"Lỗi kết nối RAGFlow: {e}")

    @staticmethod
    def build_user_message(chunk: dict, doc_type: str = "văn bản hành chính") -> str:
        """
        Xây dựng user message từ chunk data.
        """
        meta = chunk.get("meta", {})
        filename = meta.get("filename", "")
        order = meta.get("order", "?")
        total = meta.get("total_chunks", "?")

        return (
            f"Tài liệu: {filename}\n"
            f"Loại văn bản: {doc_type}\n"
            f"Chunk {order}/{total}\n"
            f"\n"
            f"--- NỘI DUNG ---\n"
            f"{chunk.get('content', '')}"
        )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((aiohttp.ClientError, RAGFlowError)),
    )
    async def send_chunk(self, session_id: str, chunk: dict, doc_type: str = "văn bản hành chính") -> dict:
        """
        Gửi 1 chunk vào RAGFlow, trả về dict kết quả.

        Returns:
        {
            "chunk_id":  str,
            "order":     int,
            "para_idxs": list[int],
            "raw_answer": str | None,
            "errors":     list[dict],
            "note":       str,
            "status":     "ok" | "failed",
        }
        """
        url = f"{self.base_url}/api/v1/chats/{self.assistant_id}/completions"
        meta = chunk.get("meta", {})
        payload = {
            "question": self.build_user_message(chunk, doc_type),
            "stream": False,
            "session_id": session_id,
        }

        session = await self._get_session()
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                answer = data["data"]["answer"]
                parsed = self.parse_llm_answer(answer)
                return {
                    "chunk_id": meta.get("chunk_id"),
                    "order": meta.get("order"),
                    "para_idxs": meta.get("para_idxs", []),
                    "raw_answer": answer,
                    "errors": parsed.get("errors", []),
                    "note": parsed.get("note", ""),
                    "status": "ok",
                }
            raise RAGFlowError(f"API trả lỗi: {data.get('message')}")

    @staticmethod
    def parse_llm_answer(answer: str) -> dict:
        """
        Parse JSON từ câu trả lời của LLM (xử lý cả markdown code block).
        """
        text = answer.strip()

        # Xóa markdown code block ```json ... ```
        if text.startswith("```"):
            lines = [l for l in text.splitlines() if not l.startswith("```")]
            text = "\n".join(lines).strip()

        # Thử parse trực tiếp
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fallback: tìm { ... } trong text
        m = re.search(r'\{.*\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass

        return {
            "errors": [],
            "note": f"Không parse được JSON. Raw: {text[:300]}",
        }

    async def send_chunks(self, chunks: list, doc_type: str = "văn bản hành chính") -> list[dict]:
        """
        Gửi nhiều chunk vào RAGFlow, trả về list kết quả.

        Mỗi chunk được gửi với session riêng.
        """
        import asyncio

        results = []
        for i, chunk in enumerate(chunks):
            try:
                sess_id = await self.create_session()
                result = await self.send_chunk(sess_id, chunk, doc_type)
                results.append(result)
            except Exception as e:
                meta = chunk.get("meta", {})
                results.append({
                    "chunk_id": meta.get("chunk_id"),
                    "order": meta.get("order"),
                    "para_idxs": meta.get("para_idxs", []),
                    "raw_answer": None,
                    "errors": [],
                    "note": str(e),
                    "status": "failed",
                })
            await asyncio.sleep(DELAY_BETWEEN_CHUNKS)

        return results

    async def close(self):
        """Đóng session"""
        if self._session and not self._session.closed:
            await self._session.close()


# Singleton instance
ragflow_client = RAGFlowClient()