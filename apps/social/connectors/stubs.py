from .base import BaseConnector, PublishResult


class InstagramConnector(BaseConnector):
    platform = 'instagram'

    def validate_account(self, social_account):
        """TODO: Validate Graph API credentials for business account."""

    def publish(self, social_account, draft_post, *, idempotency_key: str | None = None) -> PublishResult:
        return PublishResult(success=False, error='TODO: implement Instagram Graph API publishing')


class TikTokConnector(BaseConnector):
    platform = 'tiktok'

    def validate_account(self, social_account):
        """TODO: OAuth checks for TikTok Content Posting API."""

    def publish(self, social_account, draft_post, *, idempotency_key: str | None = None) -> PublishResult:
        return PublishResult(success=False, error='TODO: implement TikTok publishing')


class YouTubeConnector(BaseConnector):
    platform = 'youtube'

    def validate_account(self, social_account):
        """TODO: OAuth checks for YouTube Data API."""

    def publish(self, social_account, draft_post, *, idempotency_key: str | None = None) -> PublishResult:
        return PublishResult(success=False, error='TODO: implement YouTube publishing flow')
