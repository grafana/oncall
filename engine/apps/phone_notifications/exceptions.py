class BaseFailed(Exception):
    """
    Failed is base exception for all Failed... exceptions.
    This exception is indicates error while performing some phone notification operation.
    Optionally can contain graceful_msg attribute. When graceful_msg is provided it mean that error on provider side is
    not our fault, but some provider error (number is blocked, fraud guard, ...).
    By default, graceful_msg is None - it means that error is our fault (network problems, invalid configuration,...).

    Attributes:
       graceful_msg: string with some details about exception which can be exposed to caller.
    """

    def __init__(self, graceful_msg=None):
        self.graceful_msg = graceful_msg


class FailedToMakeCall(BaseFailed):
    pass


class FailedToSendSMS(BaseFailed):
    pass


class FailedToStartVerification(BaseFailed):
    pass


class FailedToFinishVerification(BaseFailed):
    pass


class NumberNotVerified(Exception):
    pass


class NumberAlreadyVerified(Exception):
    pass


class ProviderNotSupports(Exception):
    pass


class CallsLimitExceeded(Exception):
    pass


class SMSLimitExceeded(Exception):
    pass
