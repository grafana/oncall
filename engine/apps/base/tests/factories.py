import factory

from apps.base.models import LiveSetting, UserNotificationPolicy, UserNotificationPolicyLogRecord


class UserNotificationPolicyFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserNotificationPolicy


class UserNotificationPolicyLogRecordFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserNotificationPolicyLogRecord


class LiveSettingFactory(factory.DjangoModelFactory):
    class Meta:
        model = LiveSetting
