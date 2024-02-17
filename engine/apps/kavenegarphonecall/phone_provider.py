from kavenegar import *

import typing
import logging
from django.conf import settings
from apps.base.models import LiveSetting
from apps.base.utils import live_settings
from apps.phone_notifications.exceptions import (
    FailedToFinishVerification,
    FailedToMakeCall,
    FailedToSendSMS,
    FailedToStartVerification,
)
from apps.phone_notifications.phone_provider import PhoneProvider, ProviderFlags
from random import randint
from django.core.cache import cache

logger = logging.getLogger(__name__)


class KaveNegarPhoneProvider(PhoneProvider):
    
    def __init__(self):
        
        self.api=KavenegarAPI(
        settings.KAVENEGAR_API_KEY
        )
        
        self.verification_sms_template=settings.KAVENEGAR_VERIFICATION_SMS_TEMPLATE
        
    def make_notification_call(self, number: str, text: str):
        self.make_call(number, text)

    def send_notification_sms(self, number: str, message: str):
        self.send_sms(number, message)

    def make_call(self, number: str, text: str):
        params = {
            "receptor": number,
            "message": text,
        }
        try:
            response = self.api.call_maketts(params)
            logger.info(f"KaveNegarPhoneProvider.make_call: {response.data}")

        
        except Exception as e:
            logger.error(f"KaveNegarPhoneProvider.make_call: failed {e}")
            raise FailedToMakeCall

    def send_sms(self, number: str, text: str):
        
        params = {
        "receptor": number,
        "message": text,
        }
        try:
            response = self.api.sms_send(params)
            logger.info(f"KaveNegarPhoneProvider.make_call: {response.data}")
        
        except Exception as e:
            logger.error(f"KaveNegarPhoneProvider.send_sms: failed {e}")
            raise FailedToSendSMS

    def send_verification_sms(self, number: str):
        code = str(randint(100000, 999999))
        cache.set(self._cache_key(number), code, timeout=10 * 60)
            
        params={
            "receptor":number,
            "token":code,
            "template":self.verification_sms_template,
            "type":"sms"
        }
        
        try:
            response = self.api.verify_lookup(params)
            logger.info(f"KaveNegarPhoneProvider.make_call: {response.data}")
            
        except Exception as e:
            logger.error(f"KaveNegarPhoneProvider.send_verification_sms: failed {e}")
            raise FailedToStartVerification
    

    # def make_verification_call(self, number: str):
    #     """
    #     make_verification_call starts phone number verification by calling to user

    #     Args:
    #         number: number to verify

    #     Raises:
    #         FailedToStartVerification: if some exception in external provider occurred
    #         ProviderNotSupports: if concrete provider not phone number verification via call
    #     """
    #     raise ProviderNotSupports

    def finish_verification(self, number: str, code: str):
        
        has = cache.get(self._cache_key(number))
        if has is not None and has == code:
            return number
        else:
            return None
        

    def _cache_key(self, number):
        return f"kavenegar_provider_{number}"


    @property
    def flags(self) -> ProviderFlags:
        return ProviderFlags(
            configured=True,
            test_sms=True,
            test_call=False,
            verification_call=False,
            verification_sms=True,
        )
