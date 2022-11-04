from django.db import models


class MatrixUserIdentity(models.Model):
    # Django automatically inserts an auto-incrementing "id" field, so no need to specify it
    user_id = models.CharField(max_length=100, null=True, blank=True)
    paging_room_id = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return self.user_id if self.user_id else "[null]"
