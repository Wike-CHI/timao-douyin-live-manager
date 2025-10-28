import math
from pathlib import Path

from server.utils.ai_usage_monitor import AIUsageMonitor, ModelPricing


def test_calculate_cost_supports_alias():
    """别名（带后缀的模型名）应映射到正确的定价表。"""
    alias_cost = ModelPricing.calculate_cost("qwen-max-longcontext", 1000, 0)
    base_cost = ModelPricing.calculate_cost("qwen-max", 1000, 0)
    assert alias_cost == base_cost
    assert alias_cost > 0


def test_record_usage_accepts_explicit_cost(tmp_path: Path):
    """record_usage 应尊重外部成本并正确聚合 token 信息。"""
    monitor = AIUsageMonitor(data_dir=tmp_path)

    record = monitor.record_usage(
        model="gpt-4o-mini-2024-07-18",
        function="gateway_openai",
        input_tokens=100,
        output_tokens=50,
        total_tokens=200,
        cost=2.3456,
        duration_ms=120.0,
        success=True,
        user_id="user-1",
        anchor_id="anchor-1",
        session_id="session-1",
    )

    assert math.isclose(record.cost, 2.3456, rel_tol=1e-9)
    assert record.total_tokens == 200

    summary = monitor.get_daily_summary(days_ago=0)
    # 顶层合计会四舍五入到两位小数
    assert summary.total_tokens == 200
    assert math.isclose(summary.total_cost, 2.35, rel_tol=0, abs_tol=1e-6)

    # by_model 应带有 display_name 并保持 6 位精度的成本
    model_stats = summary.by_model["gpt-4o-mini-2024-07-18"]
    assert model_stats["display_name"] == ModelPricing.get_model_display_name("gpt-4o-mini-2024-07-18")
    assert model_stats["total_tokens"] == 200
    assert math.isclose(model_stats["cost"], 2.3456, rel_tol=1e-9)

    # 其它维度应包含输入/输出 token 统计
    function_stats = summary.by_function["gateway_openai"]
    assert function_stats["input_tokens"] == 100
    assert function_stats["output_tokens"] == 50
    assert function_stats["total_tokens"] == 200

    user_stats = summary.by_user["user-1"]
    assert user_stats["input_tokens"] == 100
    assert user_stats["output_tokens"] == 50

    anchor_stats = summary.by_anchor["anchor-1"]
    assert anchor_stats["total_tokens"] == 200


def test_qwen3_max_pricing_respects_free_allowance():
    """qwen3-max 输入前 32K token 免费，超出部分按 0.006 元/1K 计费。"""
    free_cost = ModelPricing.calculate_cost("qwen3-max", 32000, 0)
    assert math.isclose(free_cost, 0.0, abs_tol=1e-9)

    input_tokens = 42000  # 10K token 需要计费
    expected_input_cost = ((input_tokens - 32000) / 1000) * 0.006
    overage_cost = ModelPricing.calculate_cost("qwen3-max", input_tokens, 0)
    assert math.isclose(overage_cost, expected_input_cost, rel_tol=0, abs_tol=1e-9)

    expected_total = expected_input_cost + 0.06  # 输出 1K token
    total_cost = ModelPricing.calculate_cost("qwen3-max", input_tokens, 1000)
    assert math.isclose(total_cost, expected_total, rel_tol=0, abs_tol=1e-9)
