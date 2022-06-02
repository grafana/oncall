class SlackAPIException(Exception):
    def __init__(self, *args, **kwargs):
        self.response = {}
        if "response" in kwargs:
            self.response = kwargs["response"]
        super().__init__(*args)


class SlackAPITokenException(SlackAPIException):
    pass


class SlackAPIChannelArchivedException(SlackAPIException):
    pass


class SlackAPIRateLimitException(SlackAPIException):
    pass


class SlackClientException(Exception):
    pass
