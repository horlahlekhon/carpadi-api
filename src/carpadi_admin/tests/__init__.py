import django.test

from src.models.models import User


class BaseTest(django.test.TestCase):
    def setUp(self) -> None:
        self.admin: User = User.objects.create_superuser("admin", email="admin@localhost", password="passersby")
