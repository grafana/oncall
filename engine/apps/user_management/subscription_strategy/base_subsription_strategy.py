from abc import ABC, abstractmethod


class BaseSubscriptionStrategy(ABC):
    def __init__(self, organization):
        self.organization = organization

    @abstractmethod
    def phone_calls_left(self, user):
        raise NotImplementedError

    @abstractmethod
    def sms_left(self, user):
        raise NotImplementedError

    @abstractmethod
    def emails_left(self, user):
        raise NotImplementedError
