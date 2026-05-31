from typing import List, Optional, Tuple
from ...shared.config import settings
from ..check.ragflow_client import ragflow_client, RAGFlowError
from .schemas import RuleDto, RuleCreate, RuleUpdate, RuleSetDto
from fastapi import HTTPException, status

class RuleService:
    dataset_id = settings.RAGFLOW_KNOWLEDGE_DATASET_ID

    # ---------- Rule Set (Document) Operations ----------

    @staticmethod
    async def get_rule_sets(page: int = 1, limit: int = 100, search: str = ""):
        try:
            data = await ragflow_client.list_documents(
                dataset_id=RuleService.dataset_id,
                page=page,
                page_size=limit,
                search=search
            )
            # RAGFlow returns { "docs": [...], "total_datasets": ... }
            docs = data.get("docs", [])
            # Filter only .md files (Annexes/RuleSets) or keep all based on user requirement
            # The user said rule sets are .md files uploaded by IT-ADMIN
            rule_sets = []
            for doc in docs:
                # Basic mapping
                rule_sets.append({
                    "id": doc["id"],
                    "name": doc["name"],
                    "chunk_count": doc.get("chunk_count", 0),
                    "run": doc.get("run", "UNSTART"),
                    "create_date": doc.get("create_date")
                })
            return rule_sets, data.get("total_datasets", 0)
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def update_rule_set(doc_id: str, name: str):
        try:
            return await ragflow_client.update_document(
                dataset_id=RuleService.dataset_id,
                doc_id=doc_id,
                payload={"name": name}
            )
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def delete_rule_set(doc_id: str):
        try:
            return await ragflow_client.delete_document(
                dataset_id=RuleService.dataset_id,
                doc_id=doc_id
            )
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ---------- Individual Rule (Chunk) Operations ----------

    @staticmethod
    async def get_rules(doc_id: str, page: int = 1, limit: int = 20, keywords: str = ""):
        try:
            data = await ragflow_client.list_chunks(
                dataset_id=RuleService.dataset_id,
                doc_id=doc_id,
                page=page,
                page_size=limit,
                keywords=keywords
            )
            # RAGFlow returns { "chunks": [...], "total": ... }
            chunks = data.get("chunks", [])

            # Normalize chunks: ensure 'available' is boolean
            normalized_chunks = []
            for chunk in chunks:
                if 'available_int' in chunk and 'available' not in chunk:
                    chunk['available'] = bool(chunk['available_int'])
                elif 'available' in chunk:
                    chunk['available'] = bool(chunk['available'])
                else:
                    chunk['available'] = True

                # Normalize content
                if 'content_with_weight' in chunk and 'content' not in chunk:
                    chunk['content'] = chunk['content_with_weight']

                # Normalize keywords
                if 'important_kwd' in chunk and 'important_keywords' not in chunk:
                    chunk['important_keywords'] = chunk['important_kwd']

                # Normalize questions
                if 'question_kwd' in chunk and 'questions' not in chunk:
                    chunk['questions'] = chunk['question_kwd']

                normalized_chunks.append(chunk)

            return normalized_chunks, data.get("total", 0)
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def get_rule(doc_id: str, chunk_id: str):
        try:
            chunk = await ragflow_client.get_chunk(
                dataset_id=RuleService.dataset_id,
                doc_id=doc_id,
                chunk_id=chunk_id
            )

            # Normalize
            if 'available_int' in chunk and 'available' not in chunk:
                chunk['available'] = bool(chunk['available_int'])

            if 'content_with_weight' in chunk and 'content' not in chunk:
                chunk['content'] = chunk['content_with_weight']

            if 'important_kwd' in chunk and 'important_keywords' not in chunk:
                chunk['important_keywords'] = chunk['important_kwd']

            if 'question_kwd' in chunk and 'questions' not in chunk:
                chunk['questions'] = chunk['question_kwd']

            return chunk
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def create_rule(doc_id: str, data: RuleCreate):
        try:
            return await ragflow_client.add_chunk(
                dataset_id=RuleService.dataset_id,
                doc_id=doc_id,
                content=data.content,
                keywords=data.important_keywords,
                tags=data.tag_kwd,
                questions=data.questions
            )
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def update_rule(doc_id: str, chunk_id: str, data: RuleUpdate):
        try:
            payload = data.model_dump(exclude_unset=True)

            # Map 'available' boolean to 'available_int' for RAGFlow compatibility if needed
            if 'available' in payload:
                # Send both for compatibility
                payload['available_int'] = 1 if payload['available'] else 0

            import logging
            logging.info(f"Updating chunk {chunk_id} with payload: {payload}")

            return await ragflow_client.update_chunk(
                dataset_id=RuleService.dataset_id,
                doc_id=doc_id,
                chunk_id=chunk_id,
                payload=payload
            )
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def delete_rules(doc_id: str, chunk_ids: List[str]):
        try:
            return await ragflow_client.delete_chunks(
                dataset_id=RuleService.dataset_id,
                doc_id=doc_id,
                chunk_ids=chunk_ids
            )
        except RAGFlowError as e:
            raise HTTPException(status_code=500, detail=str(e))
