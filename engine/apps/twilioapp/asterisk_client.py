import logging
import requests
import json
from random import randint
from django.apps import apps
from apps.base.utils import live_settings
from apps.twilioapp.constants import TEST_CALL_TEXT
logger = logging.getLogger(__name__)

NUM_TO_WORD_DICT = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine"
]

class AsteriskClient:
    @property
    def asterisk_caller_id():
        return live_settings.ASTERISK_ARI_CALLER_ID

    def make_test_call(self, to):
        message = TEST_CALL_TEXT.format(
            channel_name="Test call",
            alert_group_name="Test notification",
            alerts_count=2
        )
        self.make_call(message=message, to=to)

    def make_call(self, message, to):
        rq_headers = {
            "Content-Type": "application/json"
        }

        destination = to[1:]

        rq_params = {
            "api_key": live_settings.ASTERISK_ARI_APIKEY,
            "callerId": live_settings.ASTERISK_ARI_CALLER_ID,
            "endpoint": f"PJSIP/{destination}@{live_settings.ASTERISK_ARI_TRUNK_NAME}",
            "extension": live_settings.ASTERISK_ARI_EXTENSION,
            "context": live_settings.ASTERISK_ARI_CONTEXT
        }

        rq_payload = json.dumps({
            "variables": {
                "alertMessage": message
            }
        })

        logging.warning(rq_params)

        try:
            requests.post(
                live_settings.ASTERISK_ARI_ENDPOINT + '/channels',
                params=rq_params,
                headers=rq_headers,
                data=rq_payload
            )
        except Exception as e:
            logger.exception("Can't make phone call: ", e)

    def create_log_record(self, **kwargs):
        AsteriskLogRecord = apps.get_model("twilioapp", "AsteriskLogRecord")
        AsteriskLogRecord.objects.create(**kwargs)

    def generate_otp(self):
        otp = ""
        hearable_otp = ""

        for _ in range(6):
            random_int = randint(0,9)
            otp += str(random_int)
            hearable_otp += " " + NUM_TO_WORD_DICT[random_int]

        return otp, hearable_otp
            
asterisk_client = AsteriskClient()
