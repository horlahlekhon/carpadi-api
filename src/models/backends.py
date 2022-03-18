import re

from django.contrib.auth.backends import ModelBackend

from src.models.models import User


class EmailOrUsernameOrPhoneModelBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        username = kwargs['username']
        password = kwargs['password']

        if username and re.search(r'[^@\s]+@[^@\s]+\.[^@\s]+', username):
            kwargs = {'email': username}
        elif username and re.search(r'\+?[\d]{3}[\d]{10}', username):
            kwargs = {'phone': username}
        else:
            kwargs = {'username': username}
        try:
            user = User.objects.get(**kwargs)
        except User.DoesNotExist:
            return None
        else:
            if user.is_active and user.check_password(password):
                return user

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
