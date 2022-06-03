import factory

from apps.base.models import LiveSetting, OrganizationLogRecord, UserNotificationPolicy, UserNotificationPolicyLogRecord


class UserNotificationPolicyFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserNotificationPolicy


class UserNotificationPolicyLogRecordFactory(factory.DjangoModelFactory):
    class Meta:
        model = UserNotificationPolicyLogRecord


class OrganizationLogRecordFactory(factory.DjangoModelFactory):
    description = factory.Faker("sentence", nb_words=4)

    class Meta:
        model = OrganizationLogRecord


class LiveSettingFactory(factory.DjangoModelFactory):
    class Meta:
        model = LiveSetting
