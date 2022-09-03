from django.core import validators
from django.utils.deconstruct import deconstructible


@deconstructible
class PhoneNumberValidator(validators.RegexValidator):
    regex = r"^\\+?\\d{1,4}?[-.\\s]?\\(?\\d{1,3}?\\)?[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,4}[-.\\s]?\\d{1,9}$"
    message = 'Enter a valid phone number in international format with or without delimiters'
    flags = 0


@deconstructible
class LicensePlateValidator(validators.RegexValidator):
    message = 'Enter a valid licence plate in the format xxx-xxx-xxx'
    regex = r"^[a-zA-Z]{3}-[0-9]{3}[a-zA-Z]{2}$"
    flags = 0
