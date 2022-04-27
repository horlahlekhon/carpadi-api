from django.core.exceptions import ValidationError


def validate_inspector(value):
    if not value.is_staff:
        raise ValidationError(
            _(f'user {value.username} is not an admin user'),
            params={'value': value},
        )


def checkout_transaction_validator(transaction):
    """
    Validate the transaction before checkout
    :param transaction: Transaction object
    :return: True if valid, False if not
    """
    if transaction.transaction_kind != "disbursement":
        raise ValidationError(_(f'Transaction {transaction.id} is not a disbursement'), params={'value': transaction})
    return True
