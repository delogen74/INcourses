from pathlib import Path

import requests
from django.conf import settings

from .base import BaseConnector, PublishResult
from .utils import html_to_plain_text


class TelegramConnector(BaseConnector):
    platform = 'telegram'

    def validate_account(self, social_account):
        required = {'bot_token', 'chat_id'}
        missing = required - set(social_account.credentials.keys())
        if missing:
            raise ValueError(f'Telegram credentials missing: {missing}')

    @staticmethod
    def _first_asset(draft_post):
        assets = getattr(draft_post, 'assets', None)
        if assets is None:
            return None
        if hasattr(assets, 'first'):
            return assets.first()
        if isinstance(assets, (list, tuple)):
            return assets[0] if assets else None
        return None

    def publish(self, social_account, draft_post, *, idempotency_key: str | None = None) -> PublishResult:
        self.validate_account(social_account)
        creds = social_account.credentials
        base_url = f"https://api.telegram.org/bot{creds['bot_token']}"
        text = f"{getattr(draft_post, 'title', '')}\n{html_to_plain_text(getattr(draft_post, 'content', ''))}".strip()

        first_asset = self._first_asset(draft_post)
        if first_asset:
            file_url = first_asset.file.url
            if file_url.startswith('http://') or file_url.startswith('https://'):
                response = requests.post(
                    f'{base_url}/sendPhoto',
                    data={'chat_id': creds['chat_id'], 'photo': file_url, 'caption': text[:1024]},
                    timeout=20,
                )
            else:
                local_file = Path(settings.MEDIA_ROOT) / first_asset.file.name
                with local_file.open('rb') as photo_file:
                    response = requests.post(
                        f'{base_url}/sendPhoto',
                        data={'chat_id': creds['chat_id'], 'caption': text[:1024]},
                        files={'photo': photo_file},
                        timeout=20,
                    )
        else:
            response = requests.post(
                f'{base_url}/sendMessage',
                data={'chat_id': creds['chat_id'], 'text': text},
                timeout=20,
            )
        data = response.json()
        if not data.get('ok'):
            return PublishResult(success=False, error=str(data))
        return PublishResult(success=True, external_id=str(data.get('result', {}).get('message_id', '')))
