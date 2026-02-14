from unittest.mock import MagicMock, patch

from django.test import Client, TestCase


class HealthCheckTests(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("apps.system.views.redis.from_url")
    def test_health_endpoint(self, redis_from_url):
        redis_conn = MagicMock()
        redis_conn.ping.return_value = True
        redis_from_url.return_value = redis_conn

        response = self.client.get("/health/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["db"], True)
        self.assertEqual(response.json()["redis"], True)
