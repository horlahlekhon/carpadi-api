from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'src.common'

    def ready(self):
        import uuid
        from .signals import complete_user_registeration
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save, pre_save

        User = get_user_model()
        post_save.connect(complete_user_registeration, sender=User, dispatch_uid=uuid.uuid4())
