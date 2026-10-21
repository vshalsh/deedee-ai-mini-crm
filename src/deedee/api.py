"""Local single-user API. Start with: uvicorn deedee.api:create_app --factory."""
from contextlib import asynccontextmanager
import os
from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .domain import Conflict, NotFound
from .persistence import SQLiteRepository
from .schemas import (CompanyInput, CompanyOutput, CompanyPage, ContactInput, ContactOutput,
                      ContactPage, ContextPreview, Selection, SummaryRequest, SummaryResult)
from .services import AIService, CRMService, MockProvider


def create_app(db_path: str | None = None):
    repository = SQLiteRepository(db_path or os.environ.get("DEEDEE_DB_PATH", "data/deedee.db"))

    @asynccontextmanager
    async def lifespan(app):
        repository.initialize()
        yield

    app = FastAPI(title="DeeDee CRM", version="0.1.0", lifespan=lifespan,
                  description="Local learning API. No authentication; bind to loopback only.")
    crm = CRMService(repository)
    ai = AIService(repository, MockProvider())

    @app.exception_handler(NotFound)
    async def not_found(request, exc):
        return JSONResponse(status_code=404, content={"error": {"code": "not_found", "message": str(exc)}})

    @app.exception_handler(Conflict)
    async def conflict(request, exc):
        return JSONResponse(status_code=409, content={"error": {"code": "relationship_conflict", "message": str(exc)}})

    @app.exception_handler(ValueError)
    async def bad_request(request, exc):
        return JSONResponse(status_code=422, content={"error": {"code": "invalid_request", "message": str(exc)}})

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        # Do not echo raw customer input or Pydantic exception contexts.
        details = [{"location": list(e["loc"]), "message": e["msg"]} for e in exc.errors()]
        return JSONResponse(status_code=422, content={"error": {
            "code": "invalid_request", "message": "Request validation failed.", "details": details}})

    @app.get("/health")
    def health():
        return {"status": "ok", "provider": "mock"}

    @app.post("/api/v1/companies", response_model=CompanyOutput, status_code=201)
    def create_company(data: CompanyInput):
        return crm.save("companies", data.model_dump())

    @app.get("/api/v1/companies", response_model=CompanyPage)
    def companies(q: str = Query("", max_length=200), limit: int = Query(50, ge=1, le=100),
                  offset: int = Query(0, ge=0)):
        return repository.list("companies", q=q, limit=limit, offset=offset)

    @app.get("/api/v1/companies/{record_id}", response_model=CompanyOutput)
    def company(record_id: str):
        return repository.get("companies", record_id)

    @app.put("/api/v1/companies/{record_id}", response_model=CompanyOutput)
    def update_company(record_id: str, data: CompanyInput):
        return crm.save("companies", data.model_dump(), record_id)

    @app.delete("/api/v1/companies/{record_id}", status_code=204)
    def delete_company(record_id: str):
        repository.delete("companies", record_id)
        return Response(status_code=204)

    @app.post("/api/v1/contacts", response_model=ContactOutput, status_code=201)
    def create_contact(data: ContactInput):
        return crm.save("contacts", data.model_dump())

    @app.get("/api/v1/contacts", response_model=ContactPage)
    def contacts(q: str = Query("", max_length=200), limit: int = Query(50, ge=1, le=100),
                 offset: int = Query(0, ge=0), company_id: str | None = Query(None, max_length=100)):
        return repository.list("contacts", q=q, limit=limit, offset=offset, company_id=company_id)

    @app.get("/api/v1/contacts/{record_id}", response_model=ContactOutput)
    def contact(record_id: str):
        return repository.get("contacts", record_id)

    @app.put("/api/v1/contacts/{record_id}", response_model=ContactOutput)
    def update_contact(record_id: str, data: ContactInput):
        return crm.save("contacts", data.model_dump(), record_id)

    @app.delete("/api/v1/contacts/{record_id}", status_code=204)
    def delete_contact(record_id: str):
        repository.delete("contacts", record_id)
        return Response(status_code=204)

    @app.post("/api/v1/ai/context", response_model=ContextPreview)
    def preview(selection: Selection):
        return {"records": ai.context(selection)}

    @app.post("/api/v1/ai/summarize", response_model=SummaryResult)
    def summarize(data: SummaryRequest):
        if not data.confirm:
            raise ValueError("Preview selected context, then set confirm=true to request a mock summary.")
        return ai.summarize(ai.context(data))

    return app
