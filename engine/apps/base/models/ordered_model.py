import logging
import random
import time
from functools import wraps

from django.db import IntegrityError, OperationalError, connection, models, transaction

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# TODO: comments
SQL_TO = """
UPDATE `{db_table}` `t1`
JOIN `{db_table}` `t2` on `t2`.`id` = %(id)s
SET `t1`.`order` = IF(`t1`.`id` = `t2`.`id`, null, IF(`t1`.`order` < `t2`.`order`, `t1`.`order` + 1, `t1`.`order` - 1))
WHERE {ordering_condition}
AND `t2`.`order` != %(order)s
AND `t1`.`order` >= IF(`t2`.`order` > %(order)s, %(order)s, `t2`.`order`)
AND `t1`.`order` <= IF(`t2`.`order` > %(order)s, `t2`.`order`, %(order)s)
ORDER BY IF(`t1`.`order` <= `t2`.`order`, `t1`.`order`, null) DESC, IF(`t1`.`order` >= `t2`.`order`, `t1`.`order`, null) ASC
"""

SQL_SWAP = """
UPDATE `{db_table}` `t1`
JOIN `{db_table}` `t2` on `t2`.`id` = %(id)s
SET `t1`.`order` = IF(`t1`.`id` = `t2`.`id`, null, `t2`.`order`)
WHERE {ordering_condition}
AND `t2`.`order` != %(order)s
AND (`t1`.`id` = `t2`.`id` OR `t1`.`order` = %(order)s)
ORDER BY IF(`t1`.`id` = `t2`.`id`, 0, 1) ASC
"""


def _retry(exc, max_attempts=15):
    def _retry_with_params(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return f(*args, **kwargs)
                except exc:
                    logger.debug(f"IntegrityError occurred in {f.__qualname__}. Retrying...")
                    if attempts == max_attempts - 1:
                        raise
                    attempts += 1
                    # double the sleep time each time and add some jitter
                    time.sleep(random.random())

        return wrapper

    return _retry_with_params


class OrderedModel(models.Model):
    """
    This class is intended to be used as a mixin for models that need to be ordered.

    Operations:
        - create: TODO
        - delete: TODO
        - move to: TODO
        - move to index: TODO
        - swap: TODO
        - get next: TODO
    """

    order: int = models.PositiveIntegerField(editable=False, db_index=True, null=True)
    order_with_respect_to = []

    class Meta:
        abstract = True
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["order"], name="unique_order"),
        ]

    def save(self, *args, **kwargs):
        if self.order is None:
            self._save_no_order_provided()
        else:
            super().save()

    @_retry(OperationalError)
    def delete(self, using=None, keep_parents=False):
        super().delete(using=using, keep_parents=keep_parents)

    @_retry((IntegrityError, OperationalError))
    def _save_no_order_provided(self):
        max_order = self.max_order()
        self.order = max_order + 1 if max_order is not None else 0
        super().save()

    @_retry((IntegrityError, OperationalError))
    def to(self, order):
        if order is None or order < 0:
            raise ValueError("Order must be a positive integer.")

        sql = SQL_TO.format(db_table=self._meta.db_table, ordering_condition=self._ordering_condition_sql)
        params = {"id": self.id, "order": order, **self._ordering_kwargs}

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            self._meta.model.objects.filter(pk=self.pk).update(order=order)

        self.refresh_from_db()

    def to_index(self, index):
        order = self._get_ordering_queryset().values_list("order", flat=True)[index]
        self.to(order)

    @_retry((IntegrityError, OperationalError))
    def swap(self, order):
        if order is None or order < 0:
            raise ValueError("Order must be a positive integer.")

        sql = SQL_SWAP.format(db_table=self._meta.db_table, ordering_condition=self._ordering_condition_sql)
        params = {"id": self.id, "order": order, **self._ordering_kwargs}

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            self._meta.model.objects.filter(pk=self.pk).update(order=order)

        self.refresh_from_db()

    def next(self):
        return self._get_ordering_queryset().filter(order__gt=self.order).first()

    def max_order(self):
        return self._get_ordering_queryset().aggregate(models.Max("order"))["order__max"]

    @property
    def _ordering_kwargs(self):
        return {field: getattr(self, field) for field in self.order_with_respect_to}

    def _get_ordering_queryset(self):
        return self._meta.model.objects.filter(**self._ordering_kwargs)

    @property
    def _ordering_condition_sql(self):
        ordering_parts = ["`t1`.`{0}` = %({0})s".format(field) for field in self.order_with_respect_to]
        return " AND ".join(ordering_parts)
