from django.conf import settings
from pythonjsonlogger import jsonlogger


class CustomStackdriverJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomStackdriverJsonFormatter, self).add_fields(log_record, record, message_dict)
        if (
            settings.GCP_PROJECT_ID
            and log_record["request_id"] is not None
            and len(log_record["request_id"].split("/")) == 2
        ):
            trace = log_record["request_id"].split("/")
            log_record["logging.googleapis.com/trace"] = f"projects/{settings.GCP_PROJECT_ID}/traces/{trace[0]}"
        if "levelname" in log_record:
            log_record["severity"] = log_record["levelname"]
        if "exc_info" in log_record:
            log_record["@type"] = "type.googleapis.com/google.devtools.clouderrorreporting.v1beta1.ReportedErrorEvent"
