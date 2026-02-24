from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model


class EmailOrUsernameModelBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        login = username or kwargs.get(User.USERNAME_FIELD) or kwargs.get('email')
        if login is None or password is None:
            return None

        try:
            user = User.objects.get(email__iexact=login)
        except User.DoesNotExist:
            return None

        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
