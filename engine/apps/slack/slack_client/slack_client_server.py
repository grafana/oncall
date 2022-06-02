import json

from slackclient.server import Server

from .exceptions import SlackClientException


class SlackClientServer(Server):
    def api_call(self, token, request="?", timeout=None, **kwargs):
        """
        This method is rewritten because we want to handle JSONDecodeError and add more information about response
        """
        response = self.api_requester.do(token, request, kwargs, timeout=timeout)
        response_json = {"headers": dict(response.headers)}
        resp_text = response.text
        try:
            response_json.update(json.loads(resp_text))
        except json.JSONDecodeError:
            response_json["response_text"] = resp_text
            exception_text = (
                f"Slack API Call Error: unexpected response from Slack \n"
                f"Status: {response.status_code}\nArgs: ('{request}',) \nKwargs: {kwargs} \n"
                f"Response: {response_json}"
            )
            raise SlackClientException(exception_text)
        return json.dumps(response_json)
