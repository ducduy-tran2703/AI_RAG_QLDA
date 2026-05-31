from typing import Optional, List, Tuple
from ...shared.config import settings
from ..check.ragflow_client import ragflow_client, RAGFlowError
from .schemas import KnowledgeDocUpdate, KnowledgeStatsResponse
from fastapi import UploadFile, HTTPException, status

class KnowledgeService:
    dataset_id = settings.RAGFLOW_KNOWLEDGE_DATASET_ID

    @staticmethod
    async def upload_document(file: UploadFile):
        content = await file.read()
        try:
            return await ragflow_client.upload_document(
                dataset_id=KnowledgeService.dataset_id,
                file_data=content,
                filename=file.filename
            )
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_documents(page: int = 1, limit: int = 20, search: str = ""):
        try:
            data = await ragflow_client.list_documents(
                dataset_id=KnowledgeService.dataset_id,
                page=page,
                page_size=limit,
                search=search
            )
            # RAGFlow returns { "docs": [...], "total_datasets": ... }
            return data.get("docs", []), data.get("total_datasets", 0)
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def update_document(doc_id: str, data: KnowledgeDocUpdate):
        try:
            # Note: RAGFlow update API might have specific fields
            payload = data.model_dump(exclude_unset=True)
            return await ragflow_client.update_document(
                dataset_id=KnowledgeService.dataset_id,
                doc_id=doc_id,
                payload=payload
            )
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def delete_document(doc_id: str):
        try:
            return await ragflow_client.delete_document(
                dataset_id=KnowledgeService.dataset_id,
                doc_id=doc_id
            )
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_stats():
        try:
            dataset = await ragflow_client.get_dataset(KnowledgeService.dataset_id)
            # RAGFlow dataset info has some stats
            return {
                "total_docs": dataset.get("doc_num", 0),
                "total_chunks": dataset.get("chunk_num", 0),
                "ready_docs": dataset.get("doc_num", 0), # Simplified
                "error_docs": 0,
                "size_mb": 0.0 # RAGFlow might not return this directly easily
            }
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def reindex_document(doc_id: str):
        try:
            # In RAGFlow, reindexing usually means changing status or triggering parse
            # Typically PUT /documents/{id} with run=1 triggers parsing
            return await ragflow_client.update_document(
                dataset_id=KnowledgeService.dataset_id,
                doc_id=doc_id,
                payload={"run": "1"}
            )
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))
