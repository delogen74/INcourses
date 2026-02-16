from dataclasses import dataclass


@dataclass
class PublishResult:
    success: bool
    external_id: str = ''
    error: str = ''


class BaseConnector:
    platform: str

    def publish(self, social_account, draft_post, *, idempotency_key: str | None = None) -> PublishResult:
        raise NotImplementedError

    def validate_account(self, social_account) -> None:
        raise NotImplementedError
