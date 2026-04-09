# Enterprise AI Copilot

Production-ready internal AI assistant built for secure enterprise workflows.

## Stack

- Frontend: React + TypeScript + Vite
- Backend: FastAPI + async SQLAlchemy
- LLM: Azure OpenAI
- RAG: FAISS vector store
- Agent orchestration: LangGraph
- Database: PostgreSQL
- Cache: Redis
- Deployment: Docker + Docker Compose

## Project Structure

```text
backend/
  app/
    agents/
    api/
    core/
    db/
    schemas/
    services/
  Dockerfile
  requirements.txt
frontend/
  src/
    api/
    components/
  Dockerfile
  nginx.conf
.env.example
docker-compose.yml
README.md
```

## Key Capabilities

- Secure document upload with role-aware metadata
- PDF, DOCX, TXT, and Markdown ingestion
- Chunking, embedding, and FAISS indexing
- Grounded answers with citations
- LangGraph multi-agent workflow:
  - `Retriever Agent`
  - `Reasoning Agent`
  - `Validator Agent`
  - `Action Agent`
- Streaming chat responses over SSE
- Redis response caching
- Token usage estimation for cost tracking
- Basic role-based access through request headers
- Query logging for auditability
- Model routing for simple vs complex prompts

## Environment Setup

1. Copy `.env.example` to `.env`
2. Fill in Azure OpenAI values
3. Start the stack

```bash
docker compose up --build
```

Frontend: http://localhost:3000  
Backend: http://localhost:8000  
Health: http://localhost:8000/health

## Local Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### `POST /upload`

Uploads and indexes a document.

Headers:
- `x-user-id: jane.doe`
- `x-user-role: analyst`

Form fields:
- `file`: binary file
- `allowed_roles`: comma-separated roles, for example `viewer,analyst`

Example:

```bash
curl -X POST http://localhost:8000/upload \
  -H "x-user-id: jane.doe" \
  -H "x-user-role: analyst" \
  -F "file=@./sample-policy.pdf" \
  -F "allowed_roles=viewer,analyst,manager"
```

### `POST /chat`

Streaming SSE chat endpoint.

```bash
curl -N -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "x-user-id: jane.doe" \
  -H "x-user-role: analyst" \
  -d '{"message":"Summarize the uploaded AML policy.","task_type":"summarize","stream":true}'
```

### `POST /query`

Non-streaming LangGraph multi-agent workflow.

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "x-user-id: jane.doe" \
  -H "x-user-role: analyst" \
  -d '{"message":"Generate an email explaining the new KYC review workflow.","task_type":"email"}'
```

## Security Notes

- Role checks are header-based for demo simplicity and should be replaced with SSO or JWT in production.
- Azure OpenAI credentials stay server-side.
- Retrieval filters document chunks by role metadata.
- Query history is persisted for audit use cases.

## Production Hardening Suggestions

- Replace header auth with Azure AD or enterprise SSO
- Add Alembic migrations
- Add object storage for documents
- Add stronger PII redaction and DLP controls
- Add unit, integration, and load tests
- Switch FAISS to Azure AI Search for distributed retrieval
# EnterpriseCopilot
