import requests

from apps.aliyun_dyvms.models import AliyunDyvmsCallStatuses
from common.custom_celery_tasks import shared_dedicated_queue_retry_task
from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase
from django.conf import settings
from celery.utils.log import get_task_logger
from celery.exceptions import Retry
from apps.base.utils import live_settings
from aliyunsdkcore.client import AcsClient
from aliyunsdkdyvmsapi.request.v20170525.QueryCallDetailByCallIdRequest import QueryCallDetailByCallIdRequest
import datetime
from typing import cast

MAX_RETRIES = 1 if settings.DEBUG else 100

logger = get_task_logger(__name__)


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


@shared_dedicated_queue_retry_task(autoretry_for=(Exception,), default_retry_delay=5, max_retries=MAX_RETRIES)
def record_call_status_async(call_id: str):
    client = AcsClient(
        live_settings.ALIYUN_DYVMS_ACCESS_KEY_ID,
        live_settings.ALIYUN_DYVMS_ACCESS_KEY_SECRET)
    queryRequest = QueryCallDetailByCallIdRequest()
    queryRequest.set_CallId(call_id)

    # 语音通话
    queryRequest.set_ProdId(live_settings.ALIYUN_DYVMS_NOTIFICATION_PROD_ID)

    oneHourAgo = datetime.datetime.utcnow() - datetime.timedelta(hours=1)

    queryRequest.set_QueryDate(int(oneHourAgo.timestamp()) * 1000)
    res = client.do_action_with_exception(queryRequest)
    acs_response_from_json: AcsResponse = AcsResponse.from_json(res)
    state = cast(QueryCallDetailByCallIdResponse,
                 (QueryCallDetailByCallIdResponse.from_json(acs_response_from_json.Data))).state
    success_statuses = [AliyunDyvmsCallStatuses.USER_COMPLETED,
                        AliyunDyvmsCallStatuses.USER_ABORTED, AliyunDyvmsCallStatuses.USER_BUSY,
                        AliyunDyvmsCallStatuses.USER_NO_ANSWER, AliyunDyvmsCallStatuses.USER_DENIED,
                        AliyunDyvmsCallStatuses.USER_NOT_IN_ZONE, AliyunDyvmsCallStatuses.USER_POWER_OFF,
                        AliyunDyvmsCallStatuses.USER_PHONE_OFF]
    if state not in success_statuses:
        raise Exception(f'retry query call_id: {call_id}, code: {acs_response_from_json.Code}, state: {state}')

    call_res = requests.post(f'{live_settings.SLACK_INSTALL_RETURN_REDIRECT_HOST}/aliyun_dyvms/call_status_events',
                             acs_response_from_json.Data.encode("utf-8"))
    if call_res.status_code != 200:
        raise Exception(f'retry query call_id: {call_id}, code: {acs_response_from_json.Code}, state: {state}'
                        f'callback result: {call_res.content.decode("utf-8")}, callback code: {call_res.status_code}')
    logger.info(f'call_id: {call_id}, code: {acs_response_from_json.Code}, state: {state}, '
                f'callback result: {call_res.content.decode("utf-8")}')
