import logging
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import get_services, get_user_context
from app.core.security import VALID_ROLES, can_upload
from app.db.models import DocumentRecord
from app.db.session import SessionLocal
from app.schemas.document import UploadResponse
from app.services.service_registry import ServiceRegistry

router = APIRouter(tags=["upload"])
logger = logging.getLogger(__name__)


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    allowed_roles: str = Form("viewer,analyst,manager,admin"),
    user=Depends(get_user_context),
    services: ServiceRegistry = Depends(get_services),
) -> UploadResponse:
    logger.info("upload.request.received")
    if not can_upload(user.role):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges to upload")

    normalized_roles = sorted({role.strip().lower() for role in allowed_roles.split(",") if role.strip().lower() in VALID_ROLES})
    if not normalized_roles:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No valid allowed_roles provided")

    document_id = str(uuid.uuid4())
    documents, storage_path = await services.document_processor.to_documents(file, normalized_roles, user.user_id, document_id)
    chunks_indexed = await services.rag_service.add_documents(documents)

    try:
        async with SessionLocal() as session:
            session.add(
                DocumentRecord(
                    id=uuid.UUID(document_id),
                    filename=file.filename or "uploaded-file",
                    content_type=file.content_type or "application/octet-stream",
                    uploaded_by=user.user_id,
                    allowed_roles={"roles": normalized_roles},
                    storage_path=storage_path,
                )
            )
            await session.commit()
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to save metadata: {exc}") from exc

    logger.info("upload.request.completed")

    return UploadResponse(
        document_id=document_id,
        filename=file.filename or "uploaded-file",
        chunks_indexed=chunks_indexed,
        allowed_roles=normalized_roles,
    )
