class OperationCouldNotBePerformedError(Exception):
    """
    Indicates that operation could not be performed due to application logic.
    E.g. you can't ack resolved AlertGroup
    """

    pass


class MaintenanceCouldNotBeStartedError(OperationCouldNotBePerformedError):
    pass


class TeamCanNotBeChangedError(OperationCouldNotBePerformedError):
    pass


class UnableToSendDemoAlert(OperationCouldNotBePerformedError):
    pass


class UserNotificationPolicyCouldNotBeDeleted(OperationCouldNotBePerformedError):
    pass


class BacksyncIntegrationRequestError(Exception):
    """Error making request to alert receive channel backsync connection."""

    def __init__(self, *args, **kwargs):
        self.error_msg = kwargs.pop("error_msg", None)
        super().__init__(*args, **kwargs)
