import logging
from dataclasses import dataclass
from dataclasses_json import dataclass_json, LetterCase, Undefined
from rest_framework import status
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.base.utils import live_settings
from typing import List, cast

from .models.phone_call import AliyunDyvmsPhoneCall
from .status_callback import update_aliyun_dyvms_call_status

logger = logging.getLogger(__name__)


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

#   {
#     "a_start_time": "2023-07-04 22:09:12",
#     "a_ring_time": "2023-07-04 22:09:08",
#     "status_code": "200100",
#     "callee": "13122042323",
#     "ring_time": "2023-07-04 22:09:24",
#     "a_duration": 22,
#     "duration": "8",
#     "a_originate_time": "2023-07-04 22:08:58",
#     "voice_type": "voice",
#     "b_duration": 8,
#     "originate_time": "2023-07-04 22:09:15",
#     "b_ring_time": "2023-07-04 22:09:24",
#     "b_start_time": "2023-07-04 22:09:26",
#     "a_end_time": "2023-07-04 22:09:33",
#     "b_originate_time": "2023-07-04 22:09:15",
#     "end_time": "2023-07-04 22:09:33",
#     "callee_show_num": "01051272364",
#     "call_id": "114018005245^100828655245",
#     "start_time": "2023-07-04 22:09:26",
#     "caller": "17863130137",
#     "b_end_time": "2023-07-04 22:09:33",
#     "status_msg": "呼叫结束（双呼）",
#     "caller_show_num": "01051272364",
#     "out_id": "abcdefgh",
#     "toll_type": "DOMESTIC"
#   }
@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class VoiceReport:
    a_start_time: str = ""
    a_ring_time: str = ""
    status_code: str = ""
    callee: str = ""
    ring_time: str = ""
    a_duration: int = -1
    duration: str = ""
    a_originate_time: str = ""
    voice_type: str = ""
    b_duration: int = -1
    originate_time: str = ""
    b_ring_time: str = ""
    b_start_time: str = ""
    a_end_time: str = ""
    b_originate_time: str = ""
    end_time: str = ""
    callee_show_num: str = ""
    call_id: str = ""
    start_time: str = ""
    caller: str = ""
    b_end_time: str = ""
    status_msg: str = ""
    caller_show_num: str = ""
    out_id: str = ""
    toll_type: str = ""
    hangup_direction: str = ""


class AllowOnlyAliyunDyvms(BasePermission):
    def has_permission(self, request, view):
        logger.info("test log")
        callDetail = cast(QueryCallDetailByCallIdResponse, QueryCallDetailByCallIdResponse.from_json(request.body))
        if not callDetail:
            return False
        call_id = callDetail.callId
        if not call_id:
            return False

        call = AliyunDyvmsPhoneCall.objects.filter(call_id=call_id).first()
        if call:
            return True
        return False

# Receive Call Status from Aliyun
class CallStatusCallback(APIView):
    permission_classes = [AllowOnlyAliyunDyvms]

    def post(self, request):
        self._handle_call_status(request)
        return Response(data={"code": 0, "msg": "成功"}, status=status.HTTP_200_OK)

    def _handle_call_status(self, request):
        callDetail = cast(QueryCallDetailByCallIdResponse, QueryCallDetailByCallIdResponse.from_json(request.body))
        try:
            logger.info(f"AliyunDyvmsPhoneProvider._handle_call_status: {callDetail}")
            update_aliyun_dyvms_call_status(call_id=callDetail.callId, status_code=callDetail.state)
        except Exception as e:
            logger.error(f"AliyunDyvmsPhoneProvider._handle_call_status: {e}, {callDetail}")
