from django.db import models

from engine.celery import app


class FailedToInvokeCeleryTask(models.Model):
    name = models.CharField(max_length=500)
    parameters = models.JSONField()

    is_sent = models.BooleanField(default=False)

    def send(self):
        app.send_task(
            name=self.name,
            args=self.parameters.get("args", []),
            kwargs=self.parameters.get("kwargs", {}),
            **self.parameters.get("options", {}),
        )
