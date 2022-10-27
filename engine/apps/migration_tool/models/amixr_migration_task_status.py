from celery import uuid as celery_uuid
from django.db import models


class AmixrMigrationTaskStatusQuerySet(models.QuerySet):
    def get_migration_task_id(self, organization_id, name):
        migrate_schedules_task_id = celery_uuid()
        self.model(organization_id=organization_id, name=name, task_id=migrate_schedules_task_id).save()
        return migrate_schedules_task_id


class AmixrMigrationTaskStatus(models.Model):
    objects = AmixrMigrationTaskStatusQuerySet.as_manager()

    task_id = models.CharField(max_length=500, db_index=True)
    name = models.CharField(max_length=500)
    organization = models.ForeignKey(
        to="user_management.Organization",
        related_name="migration_tasks",
        on_delete=models.deletion.CASCADE,
    )
    started_at = models.DateTimeField(auto_now_add=True)
    is_finished = models.BooleanField(default=False)

    def update_status_to_finished(self):
        self.is_finished = True
        self.save(update_fields=["is_finished"])
