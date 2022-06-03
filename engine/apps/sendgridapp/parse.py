import base64
import email
import mimetypes

from six import iteritems
from werkzeug.utils import secure_filename


class Parse(object):
    """Parse data received from the SendGrid Inbound Parse webhook.
    It's based on https://github.com/sendgrid/sendgrid-python/blob/master/sendgrid/helpers/inbound/parse.py
    """

    def __init__(self, request):
        self._keys = [
            "attachments",
            "headers",
            "text",
            "envelope",
            "to",
            "html",
            "sender_ip",
            "attachment-info",
            "subject",
            "dkim",
            "SPF",
            "charsets",
            "content-ids",
            "spam_report",
            "spam_score",
            "email",
        ]
        self._request = request
        self._payload = request.POST.dict()
        self._raw_payload = request.POST

    def key_values(self):
        """
        Return a dictionary of key/values in the payload received from
        the webhook
        """
        key_values = {}
        for key in self.keys:
            if key in self.payload:
                key_values[key] = self.payload[key]
        return key_values

    def get_raw_email(self):
        """
        This only applies to raw payloads:
        https://sendgrid.com/docs/Classroom/Basics/Inbound_Parse_Webhook/setting_up_the_inbound_parse_webhook.html#-Raw-Parameters
        """
        if "email" in self.payload:
            raw_email = email.message_from_string(self.payload["email"])
            return raw_email
        else:
            return None

    def attachments(self):
        """Returns an object with:
        type = file content type
        file_name = the name of the file
        contents = base64 encoded file contents"""
        attachments = None
        if "attachment-info" in self.payload:
            attachments = self._get_attachments(self.request)
        # Check if we have a raw message
        raw_email = self.get_raw_email()
        if raw_email is not None:
            attachments = self._get_attachments_raw(raw_email)
        return attachments

    def _get_attachments(self, request):
        attachments = []
        for _, filestorage in iteritems(request.files):
            attachment = {}
            if filestorage.filename not in (None, "fdopen", "<fdopen>"):
                filename = secure_filename(filestorage.filename)
                attachment["type"] = filestorage.content_type
                attachment["file_name"] = filename
                attachment["contents"] = base64.b64encode(filestorage.read())
                attachments.append(attachment)
        return attachments

    def _get_attachments_raw(self, raw_email):
        attachments = []
        counter = 1
        for part in raw_email.walk():
            attachment = {}
            if part.get_content_maintype() == "multipart":
                continue
            filename = part.get_filename()
            if not filename:
                ext = mimetypes.guess_extension(part.get_content_type())
                if not ext:
                    ext = ".bin"
                filename = "part-%03d%s" % (counter, ext)
            counter += 1
            attachment["type"] = part.get_content_type()
            attachment["file_name"] = filename
            attachment["contents"] = part.get_payload(decode=False)
            attachments.append(attachment)
        return attachments

    @property
    def keys(self):
        return self._keys

    @property
    def request(self):
        return self._request

    @property
    def payload(self):
        return self._payload

    @property
    def raw_payload(self):
        return self._raw_payload
