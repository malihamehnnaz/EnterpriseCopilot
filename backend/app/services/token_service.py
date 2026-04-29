from app.schemas.common import TokenUsage


class TokenService:
    """Provides lightweight token estimation for observability and cost tracking."""

    @staticmethod
    def estimate_tokens(text: str) -> int:
        if not text:
            return 0
        return max(1, len(text) // 4)

    def build_usage(self, prompt: str, completion: str) -> TokenUsage:
        prompt_tokens = self.estimate_tokens(prompt)
        completion_tokens = self.estimate_tokens(completion)
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
        )
