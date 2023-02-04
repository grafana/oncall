from abc import ABC, abstractmethod


class PhoneClient(ABC):
    @abstractmethod
    def make_test_call(self, to):
        pass

    @abstractmethod
    def make_call(self, message, to):
        pass

    @abstractmethod
    def create_log_record(self, **kwargs):
        pass

    @abstractmethod
    def send_otp(self, user):
        pass

    @abstractmethod
    def verify_otp(self, user, code):
        pass

    @abstractmethod
    def notify_about_changed_verified_phone_number(self, text, phone_number):
        pass
