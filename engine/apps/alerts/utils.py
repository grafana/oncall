import ipaddress
import json
import socket
from typing import Tuple
from urllib.parse import urlparse

import requests

from apps.base.utils import live_settings


def render_relative_timeline(log_created_at, alert_group_started_at):
    time_delta = log_created_at - alert_group_started_at
    seconds = int(time_delta.total_seconds())
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if days > 0:
        return "%dd%dh%dm%ds" % (days, hours, minutes, seconds)
    elif hours > 0:
        return "%dh%dm%ds" % (hours, minutes, seconds)
    elif minutes > 0:
        return "%dm%ds" % (minutes, seconds)
    else:
        return "%ds" % (seconds,)


# TODO: remove this function when we remove CustomButton model
def render_curl_command(webhook_url, http_request_type, post_kwargs):
    if http_request_type == "POST":
        curl_request = "curl -X POST"
        if "auth" in post_kwargs:
            curl_request += "\n-u ****"
        if "headers" in post_kwargs:
            curl_request += "\n-H ****"
        if "json" in post_kwargs:
            curl_request += "\n-d '{}'".format(json.dumps(post_kwargs["json"], indent=2, sort_keys=True))
        curl_request += "\n{}".format(webhook_url)
    elif http_request_type == "GET":
        curl_request = f"curl -X GET {webhook_url}"
    else:
        raise Exception("Unsupported http method")
    return curl_request


# TODO: remove this function when we remove CustomButton model
def request_outgoing_webhook(webhook_url, http_request_type, post_kwargs={}) -> Tuple[bool, str]:
    OUTGOING_WEBHOOK_TIMEOUT = 10
    if http_request_type not in ["POST", "GET"]:
        raise Exception(f"Wrong http_method parameter: {http_request_type}")

    parsed_url = urlparse(webhook_url)
    # ensure the url looks like url
    if parsed_url.scheme not in ["http", "https"]:
        return False, "Malformed url"
    if not parsed_url.netloc:
        return False, "Malformed url"
    if not live_settings.DANGEROUS_WEBHOOKS_ENABLED:
        # Get the ip address of the webhook url and check if it belongs to the private network
        try:
            webhook_url_ip_address = socket.gethostbyname(parsed_url.hostname)
        except socket.gaierror:
            return False, "Cannot resolve name in url"
        if not live_settings.DANGEROUS_WEBHOOKS_ENABLED:
            if ipaddress.ip_address(socket.gethostbyname(webhook_url_ip_address)).is_private:
                return False, "This url is not supported for outgoing webhooks"

    try:
        if http_request_type == "POST":
            r = requests.post(webhook_url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **post_kwargs)
        elif http_request_type == "GET":
            r = requests.get(webhook_url, timeout=OUTGOING_WEBHOOK_TIMEOUT)
        else:
            raise Exception()
        r.raise_for_status()
        return True, "OK 200"
    except requests.exceptions.HTTPError:
        return False, "HTTP error {}".format(r.status_code)
    except requests.exceptions.SSLError:
        return False, "ssl certificate error"
    except requests.exceptions.ConnectionError:
        return False, "Connection error happened. Probably that's because of network or proxy."
    except requests.exceptions.MissingSchema:
        return False, "Url {} is incorrect. http:// or https:// might be missing.".format(webhook_url)
    except requests.exceptions.ChunkedEncodingError:
        return False, "File content or headers might be wrong."
    except requests.exceptions.InvalidURL:
        return False, "Url {} is incorrect".format(webhook_url)
    except requests.exceptions.TooManyRedirects:
        return False, "Multiple redirects happened. That's suspicious!"
    except requests.exceptions.Timeout:
        return False, f"Request timeout {OUTGOING_WEBHOOK_TIMEOUT} secs exceeded."
    except requests.exceptions.RequestException:  # This is the correct syntax
        return False, "Failed to call outgoing webhook"
    except Exception:
        return False, "Failed to call outgoing webhook"
