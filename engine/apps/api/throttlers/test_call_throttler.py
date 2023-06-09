from rest_framework.throttling import UserRateThrottle


class TestCallThrottler(UserRateThrottle):
    """
    set a __test__ = False attribute in classes that pytest should ignore otherwise we end up getting the following:
    PytestCollectionWarning: cannot collect test class 'TestCallThrottler' because it has a __init__ constructor
    """

    __test__ = False

    scope = "make_test_call"
    rate = "5/m"


class TestPushThrottler(UserRateThrottle):
    """
    set a __test__ = False attribute in classes that pytest should ignore otherwise we end up getting the following:
    PytestCollectionWarning: cannot collect test class 'TestPushThrottler' because it has a __init__ constructor
    """

    __test__ = False

    scope = "send_test_push"
    rate = "10/m"
