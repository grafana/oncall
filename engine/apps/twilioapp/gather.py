from django.apps import apps
from django.urls import reverse
from twilio.twiml.voice_response import Gather, VoiceResponse

from apps.alerts.constants import ActionSource
from apps.twilioapp.models import TwilioPhoneCall
from common.api_helpers.utils import create_engine_url


def process_gather_data(call_sid: str, digit: str) -> VoiceResponse:
    """
    The function processes pressed digit at call time

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
        process_digit(call_sid, digit)
    else:
        # Error wrong digit pressing
        gather = Gather(action=get_gather_url(), method="POST", num_digits=1)

        response.say("Wrong digit")
        gather.say(get_gather_message())

        response.append(gather)

    return response


def process_digit(call_sid, digit):
    """
    The function get Phone Call instance according to call_sid
            and run process of pressed digit

            Args:
                call_sid (str):
                digit (str):

            Returns:

    """
    if call_sid and digit:
        twilio_phone_call = TwilioPhoneCall.objects.filter(sid=call_sid).first()
        # Check twilio phone call and then oncall phone call for backward compatibility after PhoneCall migration.
        # Will be removed soon.
        if twilio_phone_call:
            phone_call_record = twilio_phone_call.phone_call_record
        else:
            PhoneCallRecord = apps.get_model("phone_notifications", "PhoneCallRecord")
            phone_call_record = PhoneCallRecord.objects.filter(sid=call_sid).first()

        if phone_call_record is not None:
            alert_group = phone_call_record.represents_alert_group
            user = phone_call_record.receiver

            if digit == "1":
                alert_group.acknowledge_by_user(user, action_source=ActionSource.PHONE)
            elif digit == "2":
                alert_group.resolve_by_user(user, action_source=ActionSource.PHONE)
            elif digit == "3":
                alert_group.silence_by_user(user, silence_delay=1800, action_source=ActionSource.PHONE)


def get_gather_url():
    return create_engine_url(reverse("twilioapp:gather"), "https://pretty-mosh-97.loca.lt")


def get_gather_message():
    return "Press 1 to acknowledge, 2 to resolve, 3 to silence to 30 minutes"
