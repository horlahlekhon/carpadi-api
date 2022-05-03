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


def disbursement_trade_unit_validator(trade_unit):
    """
    validate the trade unit before disbursement
    """
    if trade_unit.disbursement:
        raise ValidationError(_(f'Trade unit {trade_unit.id} profits and capital has already been disbursed'), params={'value': trade_unit})
    return True