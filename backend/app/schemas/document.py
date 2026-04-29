from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    chunks_indexed: int
    allowed_roles: list[str] = Field(default_factory=list)
