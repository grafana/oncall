from rest_framework import serializers

from apps.schedules.models import OnCallSchedule


class ScheduleReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnCallSchedule
        fields = [
            "id",
            "notify_oncall_shift_freq",
            "mention_oncall_start",
            "mention_oncall_next",
            "notify_empty_oncall",
        ]
