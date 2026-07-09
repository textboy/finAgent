"""
LLM Cost Tracker - Tracks token usage and calculates costs per analysis.
"""

# Pricing per 1M tokens (USD) - {model_prefix: (input_price, output_price)}
MODEL_PRICING = {
    # ZenMux models
    "xiaomi/mimo-v2.5": (0.10, 0.30),
    "minimax/minimax-m3": (0.20, 0.60),
    "z-ai/glm-5.2": (0.15, 0.45),
    "x-ai/grok-beta": (0.10, 0.30),
    # Agnes AI models
    "agnes-2.0-flash": (0.05, 0.15),
    # Default fallback
    "default": (0.10, 0.30),
}

# Exchange rate USD -> HKD
USD_TO_HKD = 7.8

DEFAULT_PRICING = MODEL_PRICING["default"]


def get_model_pricing(model_name: str) -> tuple:
    """Get pricing for a model in HKD. Returns (input_price_per_1m, output_price_per_1m)."""
    if not model_name:
        return (DEFAULT_PRICING[0] * USD_TO_HKD, DEFAULT_PRICING[1] * USD_TO_HKD)
    # Try exact match first, then prefix match
    model_lower = model_name.lower()
    for key, pricing in MODEL_PRICING.items():
        if key in model_lower:
            return (pricing[0] * USD_TO_HKD, pricing[1] * USD_TO_HKD)
    return (DEFAULT_PRICING[0] * USD_TO_HKD, DEFAULT_PRICING[1] * USD_TO_HKD)


class CostTracker:
    """Track LLM token usage and calculate costs for a single analysis run."""

    def __init__(self):
        self.entries = []
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    def track(self, model: str, input_tokens: int, output_tokens: int):
        """Record token usage for a model."""
        if input_tokens == 0 and output_tokens == 0:
            return
        pricing = get_model_pricing(model)
        input_cost = (input_tokens / 1_000_000) * pricing[0]
        output_cost = (output_tokens / 1_000_000) * pricing[1]
        self.entries.append({
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": round(input_cost, 6),
            "output_cost": round(output_cost, 6),
            "total_cost": round(input_cost + output_cost, 6),
        })
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

    def get_total_cost(self) -> float:
        return round(sum(e["total_cost"] for e in self.entries), 6)

    def get_summary(self) -> dict:
        """Return cost summary for API response (costs in HKD, rounded to 1 decimal)."""
        total_cost = round(self.get_total_cost(), 1)
        # Aggregate by model
        by_model = {}
        for e in self.entries:
            m = e["model"]
            if m not in by_model:
                by_model[m] = {"input_tokens": 0, "output_tokens": 0, "cost": 0.0}
            by_model[m]["input_tokens"] += e["input_tokens"]
            by_model[m]["output_tokens"] += e["output_tokens"]
            by_model[m]["cost"] = round(by_model[m]["cost"] + e["total_cost"], 1)

        return {
            "total_cost": total_cost,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "by_model": by_model,
        }

    def reset(self):
        """Reset tracker for a new analysis run."""
        self.entries.clear()
        self.total_input_tokens = 0
        self.total_output_tokens = 0


# Global singleton
cost_tracker = CostTracker()
