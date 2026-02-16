from .vk import VKConnector
from .telegram import TelegramConnector
from .stubs import InstagramConnector, TikTokConnector, YouTubeConnector

CONNECTOR_MAP = {
    'vk': VKConnector,
    'telegram': TelegramConnector,
    'instagram': InstagramConnector,
    'tiktok': TikTokConnector,
    'youtube': YouTubeConnector,
}
