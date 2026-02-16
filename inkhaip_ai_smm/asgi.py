import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'inkhaip_ai_smm.settings')
application = get_asgi_application()
