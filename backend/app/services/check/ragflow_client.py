"""
RAGFlow Client — Async client for RAGFlow Chat API
====================================================
Dùng trong pipeline backend để gửi chunk đến RAGFlow và nhận kết quả LLM.
Hỗ trợ dual-assistant:
  - chunk_000 (meta)   → ASSISTANT_MANIFEST_ID (kiểm tra cấu trúc)
  - chunk_001..N       → ASSISTANT_FORMAT_ID   (kiểm tra định dạng)

Dựa trên code từ backend/source/send_to_ragflow.py v3 (dual assistant).
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

RAGFLOW_BASE_URL = settings.ragflow_base_url.rstrip("/")
RAGFLOW_API_KEY  = settings.ragflow_api_key

# Dual assistant IDs
ASSISTANT_MANIFEST_ID = settings.RAGFLOW_ASSISTANT_MANIFEST_ID  # chunk_000: kiểm tra cấu trúc
ASSISTANT_FORMAT_ID   = settings.RAGFLOW_ASSISTANT_FOMAT_ID     # chunk_001..N: kiểm tra định dạng

TIMEOUT_SECONDS      = 60
DELAY_BETWEEN_CHUNKS = 0.5


def pick_assistant(chunk: dict) -> str:
    """Chọn assistant_id phù hợp dựa vào type của chunk."""
    chunk_type = chunk.get("meta", {}).get("type", "content")
    if chunk_type == "meta":
        return ASSISTANT_MANIFEST_ID
    return ASSISTANT_FORMAT_ID


class RAGFlowError(Exception):
    """Lỗi từ RAGFlow API"""
    pass


class RAGFlowClient:
    """Async client giao tiếp với RAGFlow Chat API (dual assistant)"""

    def __init__(self):
        self.base_url = RAGFLOW_BASE_URL
        self.api_key = RAGFLOW_API_KEY
        self.manifest_assistant_id = ASSISTANT_MANIFEST_ID
        self.format_assistant_id = ASSISTANT_FORMAT_ID
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

    async def create_session(self, assistant_id: str) -> str:
        """
        Tạo session mới trên RAGFlow cho assistant cụ thể.
        Mỗi chunk dùng 1 session riêng để tránh context nhiễm.
        """
        url = f"{self.base_url}/api/v1/chats/{assistant_id}/sessions"
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
    def build_user_message(chunk: dict, total_chunks: int) -> str:
        """
        Xây dựng user message gửi vào RAGFlow.
        chunk_000: gửi thẳng nội dung manifest.
        chunk_001..N: bổ sung thêm thông tin định vị.
        """
        meta = chunk.get("meta", {})
        filename = meta.get("filename", "")
        chunk_id = meta.get("chunk_id", "")
        chunk_type = meta.get("type", "content")

        if chunk_type == "meta":
            return (
                f"Kiểm tra cấu trúc tổng thể văn bản:\n"
                f"\n"
                f"{chunk.get('content', '')}"
            )
        else:
            order = meta.get("order", "?")
            para_idxs = meta.get("para_idxs", [])
            para_range = f"{para_idxs[0]}–{para_idxs[-1]}" if para_idxs else "?"

            return (
                f"Kiểm tra định dạng đoạn văn bản:\n"
                f"Tài liệu : {filename}\n"
                f"Chunk    : {chunk_id} ({order}/{total_chunks})\n"
                f"PARA_ID  : {para_range}\n"
                f"\n"
                f"--- NỘI DUNG ---\n"
                f"{chunk.get('content', '')}"
            )

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=4),
        retry=retry_if_exception_type((aiohttp.ClientError, RAGFlowError)),
    )
    async def send_chunk(
        self,
        assistant_id: str,
        session_id: str,
        chunk: dict,
        total_chunks: int,
    ) -> dict:
        """
        Gửi 1 chunk vào RAGFlow, trả về dict kết quả.

        Returns:
        {
            "chunk_id":   str,
            "chunk_type": str,
            "order":      int,
            "para_idxs":  list[int],
            "raw_answer": str | None,
            "errors":     list[dict],
            "note":       str,
            "status":     "ok" | "failed",
        }
        """
        url = f"{self.base_url}/api/v1/chats/{assistant_id}/completions"
        meta = chunk.get("meta", {})
        payload = {
            "question": self.build_user_message(chunk, total_chunks),
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
                    "chunk_type": meta.get("type", "content"),
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

        if text.startswith("```"):
            lines = [l for l in text.splitlines() if not l.startswith("```")]
            text = "\n".join(lines).strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

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

    async def send_chunks(self, chunks: list) -> list[dict]:
        """
        Gửi nhiều chunk vào RAGFlow, mỗi chunk dùng đúng assistant.
        Trả về list kết quả.
        """
        import asyncio

        total_chunks = len(chunks)
        results = []

        for i, chunk in enumerate(chunks):
            try:
                assistant_id = pick_assistant(chunk)
                sess_id = await self.create_session(assistant_id)
                result = await self.send_chunk(assistant_id, sess_id, chunk, total_chunks)
                results.append(result)
            except Exception as e:
                meta = chunk.get("meta", {})
                results.append({
                    "chunk_id": meta.get("chunk_id"),
                    "chunk_type": meta.get("type", "content"),
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

    # ══════════════════════════════════════════════════════════════════════
    # DOCUMENT MANAGEMENT (KNOWLEDGE BASE)
    # ══════════════════════════════════════════════════════════════════════

    async def list_documents(self, dataset_id: str, page: int = 1, page_size: int = 20, search: str = ""):
        """Lấy danh sách tài liệu trong dataset"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"
        params = {"page": page, "page_size": page_size, "name": search}

        session = await self._get_session()
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                return data["data"]
            raise RAGFlowError(f"Lấy danh sách thất bại: {data.get('message')}")

    async def upload_document(self, dataset_id: str, file_data: bytes, filename: str):
        """Tải tài liệu lên dataset"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"

        # RAGFlow expects multipart/form-data
        data = aiohttp.FormData()
        data.add_field('file', file_data, filename=filename)

        session = await self._get_session()
        # Note: session headers are set to application/json by default in __init__.
        # We need to let aiohttp set the boundary for multipart.
        async with session.post(url, data=data, headers={}) as resp:
            res_data = await resp.json()
            if res_data.get("code") == 0:
                return res_data["data"]
            raise RAGFlowError(f"Tải lên thất bại: {res_data.get('message')}")

    async def update_document(self, dataset_id: str, doc_id: str, payload: dict):
        """Cập nhật thông tin/trạng thái tài liệu (ví dụ: parser_id, status)"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{doc_id}"

        session = await self._get_session()
        async with session.put(url, json=payload) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                # Trả về data hoặc thông báo thành công dưới dạng dict
                return data.get("data") if isinstance(data.get("data"), dict) else data
            raise RAGFlowError(f"Cập nhật thất bại: {data.get('message')}")

    async def delete_document(self, dataset_id: str, doc_id: str):
        """Xóa tài liệu khỏi dataset"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents"
        payload = {"ids": [doc_id]}

        session = await self._get_session()
        async with session.delete(url, json=payload) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                return True
            raise RAGFlowError(f"Xóa thất bại: {data.get('message')}")

    async def get_dataset(self, dataset_id: str):
        """Lấy thông tin dataset (để lấy stats)"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}"

        session = await self._get_session()
        async with session.get(url) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                return data["data"]
            raise RAGFlowError(f"Lấy dataset thất bại: {data.get('message')}")

    # ══════════════════════════════════════════════════════════════════════
    # CHUNK MANAGEMENT (RULES)
    # ══════════════════════════════════════════════════════════════════════

    async def list_chunks(self, dataset_id: str, doc_id: str, page: int = 1, page_size: int = 20, keywords: str = ""):
        """Lấy danh sách các chunk (Rule) của một document"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{doc_id}/chunks"
        params = {"page": page, "page_size": page_size, "keywords": keywords}

        session = await self._get_session()
        async with session.get(url, params=params) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                return data["data"]
            raise RAGFlowError(f"Lấy danh sách chunk thất bại: {data.get('message')}")

    async def get_chunk(self, dataset_id: str, doc_id: str, chunk_id: str):
        """Lấy thông tin chi tiết của một chunk"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{doc_id}/chunks/{chunk_id}"

        session = await self._get_session()
        async with session.get(url) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                return data["data"]
            raise RAGFlowError(f"Lấy chi tiết chunk thất bại: {data.get('message')}")

    async def add_chunk(self, dataset_id: str, doc_id: str, content: str, keywords: list = None, tags: list = None, questions: list = None):
        """Tạo mới một chunk (Rule)"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{doc_id}/chunks"
        payload = {
            "content": content,
            "important_keywords": keywords or [],
            "tag_kwd": tags or [],
            "questions": questions or []
        }

        session = await self._get_session()
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                return data["data"]
            raise RAGFlowError(f"Tạo chunk thất bại: {data.get('message')}")

    async def update_chunk(self, dataset_id: str, doc_id: str, chunk_id: str, payload: dict):
        """Cập nhật nội dung/trạng thái một chunk"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{doc_id}/chunks/{chunk_id}"

        session = await self._get_session()
        async with session.patch(url, json=payload) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                # Trả về data hoặc thông báo thành công dưới dạng dict
                return data.get("data") if isinstance(data.get("data"), dict) else data
            raise RAGFlowError(f"Cập nhật chunk thất bại: {data.get('message')}")

    async def delete_chunks(self, dataset_id: str, doc_id: str, chunk_ids: list):
        """Xóa một hoặc nhiều chunk"""
        url = f"{self.base_url}/api/v1/datasets/{dataset_id}/documents/{doc_id}/chunks"
        payload = {"chunk_ids": chunk_ids}

        session = await self._get_session()
        async with session.delete(url, json=payload) as resp:
            data = await resp.json()
            if data.get("code") == 0:
                return True
            raise RAGFlowError(f"Xóa chunk thất bại: {data.get('message')}")


# Singleton instance
ragflow_client = RAGFlowClient()