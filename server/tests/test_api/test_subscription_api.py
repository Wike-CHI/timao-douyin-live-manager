"""Subscription API response tests."""

from decimal import Decimal

from fastapi.testclient import TestClient

from server.app.models.subscription import SubscriptionPlan, SubscriptionPlanTypeEnum


def create_plan(db_session) -> SubscriptionPlan:
    plan = SubscriptionPlan(
        name="pro",
        display_name="Pro Plan",
        description="Test plan",
        plan_type=SubscriptionPlanTypeEnum.BASIC,
        price=Decimal("99.99"),
        currency="CNY",
        billing_cycle=30,
        max_streams=3,
        max_storage_gb=50,
        max_ai_requests=100,
        max_export_count=10,
        features="{}",
        is_active=True,
    )
    db_session.add(plan)
    db_session.commit()
    db_session.refresh(plan)
    return plan


def test_get_subscription_plans_returns_wrapped_response(client: TestClient, db_session) -> None:
    """GET /api/subscription/plans should return BaseResponse envelope with plan data."""

    create_plan(db_session)

    response = client.get("/api/subscription/plans")
    assert response.status_code == 200
    payload = response.json()

    assert payload["success"] is True
    assert isinstance(payload["data"], list)
    assert len(payload["data"]) == 1

    plan = payload["data"][0]
    assert plan["name"] == "Pro Plan"
    assert plan["plan_type"] == "basic"
    assert plan["is_active"] is True

