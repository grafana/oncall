import logging
import re
from string import digits

from django.apps import apps
from django.urls import reverse
from phonenumbers import COUNTRY_CODE_TO_REGION_CODE
from twilio.twiml.voice_response import Gather, VoiceResponse

from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


def get_calling_code(iso):
    for code, isos in COUNTRY_CODE_TO_REGION_CODE.items():
        if iso.upper() in isos:
            return code
    return None


def get_gather_url():
    gather_url = create_engine_url(reverse("twilioapp:gather"))
    return gather_url


def get_gather_message():
    return "Press 1 to acknowledge, 2 to resolve, 3 to silence to 30 minutes"


def process_call_data(call_sid, digit):
    """The function processes pressed digit at call time

    Args:
        call_sid (str):
        digit (str): user pressed digit

    Returns:
        response (VoiceResponse)
    """

    response = VoiceResponse()

    if digit in ["1", "2", "3"]:
        # Success case
        response.say(f"You have pressed digit {digit}")

        PhoneCall = apps.get_model("twilioapp", "PhoneCall")
        PhoneCall.objects.get_and_process_digit(call_sid=call_sid, digit=digit)

    else:
        # Error wrong digit pressing
        gather = Gather(action=get_gather_url(), method="POST", num_digits=1)

        response.say("Wrong digit")
        gather.say(get_gather_message())

        response.append(gather)

    return response


def check_phone_number_is_valid(phone_number):
    return re.match(r"^\+\d{8,15}$", phone_number) is not None


def parse_phone_number(raw_phone_number):
    return "+" + "".join(c for c in raw_phone_number if c in digits)
