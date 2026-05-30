# Implementation Plan - Phase 1: Knowledge & Rules Backend

This phase focuses on building the management system for the Knowledge Base (RAG) and Rule Sets. These components are essential for the AI pipeline to function correctly.

## User Review Required

- **MinIO Storage Structure**: Knowledge documents will be stored in a separate bucket or prefix (e.g., `knowledge/`).
- **Initial Data**: Should we provide a script to seed initial categories (e.g., Thể thức, Chính tả) and standard rules (NĐ30)?

## Proposed Changes

### [Knowledge Base Module]

Implementing CRUD for Knowledge Categories and Documents.

#### [schemas.py](file:///D:/Workspace/projects/university/QLDA/AI_RAG_QLDA/backend/app/services/knowledge/schemas.py) [NEW]

- Define Pydantic models for KnowledgeCategory and KnowledgeBaseDocument (Create, Update, Response).

#### [service.py](file:///D:/Workspace/projects/university/QLDA/AI_RAG_QLDA/backend/app/services/knowledge/service.py) [NEW]

- Implement `KnowledgeService` with methods for:
    - Managing categories.
    - Uploading and managing documents.
    - Integration with MinIO for file storage.
    - (Optional) Placeholder for RAGFlow reindexing.

#### [router.py](file:///D:/Workspace/projects/university/QLDA/AI_RAG_QLDA/backend/app/services/knowledge/router.py) [NEW]

- Define API endpoints for Knowledge Base as specified in the design doc.

---

### [Rule Sets Module]

Implementing CRUD for Rule Sets and individual Rules.

#### [schemas.py](file:///D:/Workspace/projects/university/QLDA/AI_RAG_QLDA/backend/app/services/rules/schemas.py) [NEW]

- Define Pydantic models for RuleSet and Rule (Create, Update, Response).

#### [service.py](file:///D:/Workspace/projects/university/QLDA/AI_RAG_QLDA/backend/app/services/rules/service.py) [NEW]

- Implement `RuleService` with methods for:
    - Managing rule sets.
    - Managing individual rules within a set.
    - Cloning rule sets.
    - Setting a default rule set.

#### [router.py](file:///D:/Workspace/projects/university/QLDA/AI_RAG_QLDA/backend/app/services/rules/router.py) [NEW]

- Define API endpoints for Rules as specified in the design doc.

---

### [Infrastructure & Integration]

#### [main.py](file:///D:/Workspace/projects/university/QLDA/AI_RAG_QLDA/backend/app/main.py)

- Register the new routers.

## Verification Plan

### Automated Tests
- Since I cannot run the full environment easily, I will verify the code through static analysis and manual code review.
- If possible, I will create a small test script to verify the logic of services.

### Manual Verification
- I will use `analyze_file` to check for syntax and type errors in all new files.
- I will verify that the endpoints match the design document.
