import re

from django.contrib.auth.backends import ModelBackend

from src.models.models import User


# TODO verify uniqueness of imei... if the imei logging in with belongs to a different user,
#  then you cant log in to your account with a different user's phone... but is this right ?,
#  what if i sold my phone and another user bought it and want to login with the phone,
class EmailOrUsernameOrPhoneModelBackend(ModelBackend):
    def authenticate(self, request, **kwargs):
        username = str(kwargs['username']).lower()
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
