import requests
from django.conf import settings

from src.notifications.services import logger


def build_absolute_uri(path):
    return f'{settings.SITE_URL}{path}'


def check_vin(vin: str):
    headers = {"partner-token": settings.CARMD_PARTNER_TOKEN, "Authorization": settings.CARMD_APIKEY}
    response = requests.get(settings.CARMD_VIN_CHECK(vin), headers=headers)
    js = response.json()
    if response.status_code == 200 and js["message"]["message"] == "ok":
        return js["data"]
    logger.debug(f"Try to check vehicle details for vin {vin}. resp: {js}")
    return None
