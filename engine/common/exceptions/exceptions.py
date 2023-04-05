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
