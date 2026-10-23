"""Routes for the sales pipeline, follow-ups, activity history, and dashboard."""
from fastapi import APIRouter, Query, Response
from .work_schemas import (DealInput, DealOutput, DealPage, TaskInput, TaskOutput, TaskPage,
                           ActivityInput, ActivityOutput, ActivityPage, Stage, TaskStatus)


def workflow_router(repository):
    router = APIRouter(prefix="/api/v1")

    @router.post("/deals", response_model=DealOutput, status_code=201)
    def create_deal(data: DealInput):
        return repository.create("deals", data.model_dump(mode="json"))

    @router.get("/deals", response_model=DealPage)
    def list_deals(q: str = Query("", max_length=200), limit: int = Query(50, ge=1, le=100),
                    offset: int = Query(0, ge=0), company_id: str | None = None, contact_id: str | None = None, stage: Stage | None = None):
        return repository.list("deals", q=q, limit=limit, offset=offset, company_id=company_id, contact_id=contact_id, stage=stage)

    @router.get("/deals/{record_id}", response_model=DealOutput)
    def get_deal(record_id: str):
        return repository.get("deals", record_id)

    @router.put("/deals/{record_id}", response_model=DealOutput)
    def update_deal(record_id: str, data: DealInput):
        return repository.update("deals", record_id, data.model_dump(mode="json"))

    @router.delete("/deals/{record_id}", status_code=204)
    def delete_deal(record_id: str):
        repository.delete("deals", record_id)
        return Response(status_code=204)

    @router.post("/tasks", response_model=TaskOutput, status_code=201)
    def create_task(data: TaskInput):
        return repository.create("tasks", data.model_dump(mode="json"))

    @router.get("/tasks", response_model=TaskPage)
    def list_tasks(q: str = Query("", max_length=200), limit: int = Query(50, ge=1, le=100),
                    offset: int = Query(0, ge=0), company_id: str | None = None, contact_id: str | None = None, deal_id: str | None = None, status: TaskStatus | None = None):
        return repository.list("tasks", q=q, limit=limit, offset=offset, company_id=company_id, contact_id=contact_id, deal_id=deal_id, status=status)

    @router.get("/tasks/{record_id}", response_model=TaskOutput)
    def get_task(record_id: str):
        return repository.get("tasks", record_id)

    @router.put("/tasks/{record_id}", response_model=TaskOutput)
    def update_task(record_id: str, data: TaskInput):
        return repository.update("tasks", record_id, data.model_dump(mode="json"))

    @router.delete("/tasks/{record_id}", status_code=204)
    def delete_task(record_id: str):
        repository.delete("tasks", record_id)
        return Response(status_code=204)

    @router.post("/activities", response_model=ActivityOutput, status_code=201)
    def create_activity(data: ActivityInput):
        return repository.create("activities", data.model_dump(mode="json"))

    @router.get("/activities", response_model=ActivityPage)
    def list_activities(q: str = Query("", max_length=200), limit: int = Query(50, ge=1, le=100),
                    offset: int = Query(0, ge=0), company_id: str | None = None, contact_id: str | None = None, deal_id: str | None = None):
        return repository.list("activities", q=q, limit=limit, offset=offset, company_id=company_id, contact_id=contact_id, deal_id=deal_id)

    @router.get("/activities/{record_id}", response_model=ActivityOutput)
    def get_activity(record_id: str):
        return repository.get("activities", record_id)

    @router.put("/activities/{record_id}", response_model=ActivityOutput)
    def update_activity(record_id: str, data: ActivityInput):
        return repository.update("activities", record_id, data.model_dump(mode="json"))

    @router.delete("/activities/{record_id}", status_code=204)
    def delete_activity(record_id: str):
        repository.delete("activities", record_id)
        return Response(status_code=204)

    @router.get("/deals/{record_id}/history")
    def deal_history(record_id: str):
        return repository.history(record_id)

    @router.get("/dashboard")
    def dashboard():
        return repository.dashboard()

    @router.get("/backup")
    def backup():
        return repository.backup()

    return router
