import logging
from random import randint

from django.core.cache import cache

from apps.base.utils import live_settings
from apps.phone_notifications.exceptions import FailedToMakeCall, FailedToStartVerification
from apps.phone_notifications.phone_provider import PhoneProvider, ProviderFlags
from .models.phone_call import AliyunDyvmsPhoneCall, AliyunDyvmsCallStatuses
from .tasks import record_call_status_async
from aliyunsdkcore.client import AcsClient
from aliyunsdkdyvmsapi.request.v20170525.SingleCallByTtsRequest import SingleCallByTtsRequest
from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
from aliyunsdkcore.acs_exception.exceptions import ClientException
from aliyunsdkcore.acs_exception.exceptions import ServerException

logger = logging.getLogger(__name__)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class AcsResponse:
    RequestId: str
    Message: str
    Code: str
    Data: str = ''
    CallId: str = ''

@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class QueryCallDetailByCallIdResponse:
    callId: str = ''
    endDate: str = ''
    stateDesc: str = ''
    callee: str = ''
    bStartTime: str = ''
    gmtCreate: str = ''
    duration: int = 0
    calleeShowNumber: str = ''
    bRingTime: str = ''
    bEndTime: str = ''
    state: str = ''
    startDate: str = ''
    hangupDirection: int = 0


class AliyunDyvmsPhoneProvider(PhoneProvider):
    """
    AliyunDyvmsPhoneProvider is an implementation of phone provider which supports only voice calls (https://dyvms.console.aliyun.com/overview/home).
    """

    def make_notification_call(self, number: str, message: str) -> AliyunDyvmsPhoneCall:
        logger.info(f"AliyunDyvmsPhoneProvider.make_notification_call: start")
        try:
            formated_message = f'{{"title":"{message}"}}'
            response = self._call_create(live_settings.ALIYUN_DYVMS_TTS_CODE, number, formated_message)
            acs_response_from_json: AcsResponse = AcsResponse.from_json(response)
            if acs_response_from_json.Code != "OK":
                logger.error(f'AliyunDyvmsPhoneProvider.make_notification_call to {number}: failed'
                             f'{acs_response_from_json.Code}, {acs_response_from_json.Message}')
                raise FailedToMakeCall(graceful_msg=f'Failed make notification call to {number},'
                                                    f'{acs_response_from_json.Code}, {acs_response_from_json.Message}')
            call_id = acs_response_from_json.CallId

            if not call_id:
                logger.error("AliyunDyvmsPhoneProvider.make_notification_call: failed, missing call id")
                raise FailedToMakeCall(graceful_msg=f'Failed make notification call to {number}, missing call id'
                                                    f'{acs_response_from_json.RequestId}')

            logger.info(f"AliyunDyvmsPhoneProvider.make_notification_call: success, call_id {call_id}")
            phoneCall = AliyunDyvmsPhoneCall(
                status=AliyunDyvmsCallStatuses.IN_PROCESS,
                call_id=call_id,
            )

            record_call_status_async.delay(call_id)

            return phoneCall
        except ServerException as server_err:
            logger.error(f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number {number}, {server_err}")
            raise FailedToMakeCall(graceful_msg=f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number "
                                                f"{number}, {server_err}")
        except ClientException as client_err:
            logger.error(f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number {number} {client_err}")
            raise FailedToMakeCall(graceful_msg=f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number "
                                                f"{number}, {client_err}")
        except Exception as e:
            logger.error(f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number {number} {e}")
            raise FailedToMakeCall(graceful_msg=f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number "
                                                f"{number}, {e}")

    def make_call(self, number: str, message: str):
        logger.info(f"AliyunDyvmsPhoneProvider.make_call: start")
        try:
            formated_message = f'{{"title":"{message}"}}'
            response = self._call_create(live_settings.ALIYUN_DYVMS_TTS_CODE, number, formated_message)
            acs_response_from_json: AcsResponse = AcsResponse.from_json(response)
            if acs_response_from_json.Code != "OK":
                logger.error(f'AliyunDyvmsPhoneProvider.make_notification_call to {number}: failed'
                             f'{acs_response_from_json.Code}, {acs_response_from_json.Message}')
                raise FailedToMakeCall(graceful_msg=f'Failed make notification call to {number},'
                                                    f'{acs_response_from_json.Code}, {acs_response_from_json.Message}')
            call_id = acs_response_from_json.CallId

            if not call_id:
                logger.error("AliyunDyvmsPhoneProvider.make_notification_call: failed, missing call id")
                raise FailedToMakeCall(graceful_msg=f'Failed make notification call to {number}, missing call id'
                                                    f'{acs_response_from_json.RequestId}')

            logger.info(f"AliyunDyvmsPhoneProvider.make_notification_call: success, call_id {call_id}")
        except ServerException as server_err:
            logger.error(f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number {number}, {server_err}")
            raise FailedToMakeCall(graceful_msg=f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number "
                                                f"{number}, {server_err}")
        except ClientException as client_err:
            logger.error(f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number {number} {client_err}")
            raise FailedToMakeCall(graceful_msg=f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number "
                                                f"{number}, {client_err}")

    def _call_create(self, tts_code: str, number: str, text: str):
        client = AcsClient(
            live_settings.ALIYUN_DYVMS_ACCESS_KEY_ID,
            live_settings.ALIYUN_DYVMS_ACCESS_KEY_SECRET)
        callRequest = SingleCallByTtsRequest()
        callRequest.set_CalledNumber(number)
        callRequest.set_TtsCode(tts_code)
        callRequest.set_TtsParam(text)
        callRequest.set_Speed(-150)
        callRequest.set_CalledShowNumber(live_settings.ALIYUN_DYVMS_CALLED_SHOW_NUMBER)

        res = client.do_action_with_exception(callRequest)
        return res

    def make_verification_call(self, number: str):
        code = str(randint(100000, 999999))
        codewspaces = "   ".join(code)
        cache.set(self._cache_key(number), code, timeout=10 * 60)
        message = f'{{"product":"grafana oncall", "code":"{codewspaces}"}}'
        try:
            response = self._call_create(live_settings.ALIYUN_DYVMS_VERIFY_TTS_CODE, number, message)
            acs_response_from_json: AcsResponse = AcsResponse.from_json(response)
            if acs_response_from_json.Code != "OK":
                logger.error(f'AliyunDyvmsPhoneProvider.make_notification_call to {number}: failed'
                             f'{acs_response_from_json.Code}, {acs_response_from_json.Message}')
                raise FailedToMakeCall(graceful_msg=f'Failed make notification call to {number},'
                                                    f'{acs_response_from_json.Code}, {acs_response_from_json.Message}')
            call_id = acs_response_from_json.CallId

            if not call_id:
                logger.error("AliyunDyvmsPhoneProvider.make_notification_call: failed, missing call id")
                raise FailedToMakeCall(graceful_msg=f'Failed make notification call to {number}, missing call id'
                                                    f'{acs_response_from_json.RequestId}')

            logger.info(f"AliyunDyvmsPhoneProvider.make_notification_call: success, call_id {call_id}")
        except ServerException as server_err:
            logger.error(f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number {number}, {server_err}")
            raise FailedToMakeCall(graceful_msg=f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number "
                                                f"{number}, {server_err}")
        except ClientException as client_err:
            logger.error(f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number {number} {client_err}")
            raise FailedToMakeCall(graceful_msg=f"AliyunDyvmsPhoneProvider.make_notification_call: failed, number "
                                                f"{number}, {client_err}")

    def finish_verification(self, number, code):
        has = cache.get(self._cache_key(number))
        if has is not None and has == code:
            return number
        else:
            return None

    def _cache_key(self, number):
        return f"aliyun_dyvms_provider_{number}"

    @property
    def flags(self) -> ProviderFlags:
        return ProviderFlags(
            configured=True,
            test_sms=False,
            test_call=True,
            verification_call=True,
            verification_sms=False,
        )
