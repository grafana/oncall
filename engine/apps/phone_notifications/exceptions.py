class FailedToMakeCall(Exception):
    pass


class FailedToSendSMS(Exception):
    pass


class NumberNotVerified(Exception):
    pass


class NumberAlreadyVerified(Exception):
    pass


class FailedToStartVerification(Exception):
    pass


class FailedToFinishVerification(Exception):
    pass


class ProviderNotSupports(Exception):
    pass


class CallsLimitExceeded(Exception):
    pass


class SMSLimitExceeded(Exception):
    pass
