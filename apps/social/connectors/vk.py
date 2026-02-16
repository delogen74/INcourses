import requests

from .base import BaseConnector, PublishResult
from .utils import html_to_plain_text


class VKConnector(BaseConnector):
    platform = 'vk'

    def validate_account(self, social_account):
        required = {'group_id', 'access_token'}
        missing = required - set(social_account.credentials.keys())
        if missing:
            raise ValueError(f'VK credentials missing: {missing}')

    def publish(self, social_account, draft_post, *, idempotency_key: str | None = None) -> PublishResult:
        self.validate_account(social_account)
        creds = social_account.credentials
        plain_content = html_to_plain_text(draft_post.content)
        payload = {
            'owner_id': f"-{creds['group_id']}",
            'from_group': 1,
            'message': f"{draft_post.title}\n{plain_content}".strip(),
            'access_token': creds['access_token'],
            'v': '5.199',
        }
        if idempotency_key:
            payload['guid'] = idempotency_key[:32]
        r = requests.post('https://api.vk.com/method/wall.post', data=payload, timeout=20)
        data = r.json()
        if 'error' in data:
            return PublishResult(success=False, error=str(data['error']))
        post_id = data.get('response', {}).get('post_id', '')
        return PublishResult(success=True, external_id=str(post_id))
