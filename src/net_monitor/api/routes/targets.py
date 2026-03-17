from __future__ import annotations

from fastapi import APIRouter, Query, Request

from net_monitor.storage.repositories.ping_results import PingResultRepository
from net_monitor.storage.repositories.targets import TargetRepository

router = APIRouter(prefix="/api/targets", tags=["targets"])


@router.get("")
def get_targets(request: Request) -> list[dict]:
    repository = TargetRepository(request.app.state.session_factory)
    return repository.list_targets_with_latest_status()


@router.get("/{target_id}/results")
def get_target_results(
    target_id: str,
    request: Request,
    limit: int = Query(default=200, ge=1, le=5000),
) -> dict:
    repository = PingResultRepository(request.app.state.session_factory)
    return {
        "target_id": target_id,
        "results": repository.list_results(target_id=target_id, limit=limit),
    }


@router.get("/{target_id}/summary")
def get_target_summary(target_id: str, request: Request) -> dict:
    repository = PingResultRepository(request.app.state.session_factory)
    return repository.get_summary(target_id=target_id)
