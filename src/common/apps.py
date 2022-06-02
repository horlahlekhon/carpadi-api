from django.apps import AppConfig


class CommonConfig(AppConfig):
    name = 'src.common'

    def ready(self):
        import uuid
        from .signals import complete_user_registeration, trade_unit_completed, disbursement_completed
        from django.contrib.auth import get_user_model
        from django.db.models.signals import post_save
        from django_rest_passwordreset.signals import reset_password_token_created
        from django_rest_passwordreset.views import ResetPasswordRequestToken
        from src.common.signals import password_reset_token_created
        from src.common.signals import complete_transaction
        from src.models.models import Transaction, Disbursement, TradeUnit

        User = get_user_model()
        post_save.connect(complete_user_registeration, sender=User, dispatch_uid=uuid.uuid4())
        reset_password_token_created.connect(
            password_reset_token_created, sender=ResetPasswordRequestToken, dispatch_uid=uuid.uuid4()
        )
        post_save.connect(complete_transaction, sender=Transaction, dispatch_uid=uuid.uuid4())

        post_save.connect(trade_unit_completed, sender=TradeUnit, dispatch_uid=uuid.uuid4())
        post_save.connect(disbursement_completed, sender=Disbursement, dispatch_uid=uuid.uuid4())
