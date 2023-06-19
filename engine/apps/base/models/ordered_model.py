import logging
import random
import time
import typing
from functools import wraps

from django.db import IntegrityError, OperationalError, connection, models, transaction

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Update object's order to NULL and shift other objects' orders accordingly in a single SQL query.
SQL_TO = """
UPDATE `{db_table}` `t1`
JOIN `{db_table}` `t2` ON `t2`.`{pk_name}` = %(pk)s
SET `t1`.`order` = IF(`t1`.`{pk_name}` = `t2`.`{pk_name}`, null, IF(`t1`.`order` < `t2`.`order`, `t1`.`order` + 1, `t1`.`order` - 1))
WHERE {ordering_condition}
AND `t2`.`order` != %(order)s
AND `t1`.`order` >= IF(`t2`.`order` > %(order)s, %(order)s, `t2`.`order`)
AND `t1`.`order` <= IF(`t2`.`order` > %(order)s, `t2`.`order`, %(order)s)
ORDER BY IF(`t1`.`order` <= `t2`.`order`, `t1`.`order`, null) DESC, IF(`t1`.`order` >= `t2`.`order`, `t1`.`order`, null) ASC
"""

# Update object's order to NULL and set the other object's order to specified value in a single SQL query.
SQL_SWAP = """
UPDATE `{db_table}` `t1`
JOIN `{db_table}` `t2` ON `t2`.`{pk_name}` = %(pk)s
SET `t1`.`order` = IF(`t1`.`{pk_name}` = `t2`.`{pk_name}`, null, `t2`.`order`)
WHERE {ordering_condition}
AND `t2`.`order` != %(order)s
AND (`t1`.`{pk_name}` = `t2`.`{pk_name}` OR `t1`.`order` = %(order)s)
ORDER BY IF(`t1`.`{pk_name}` = `t2`.`{pk_name}`, 0, 1) ASC
"""


def _retry(exc: typing.Type[Exception] | tuple[typing.Type[Exception], ...], max_attempts: int = 15) -> typing.Callable:
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
    It's similar to django-ordered-model: https://github.com/django-ordered-model/django-ordered-model.
    The key difference of this implementation is that it allows orders to be unique at the database level and
    is designed to work correctly under concurrent load.

    Notable differences compared to django-ordered-model:
        - order can be unique at the database level;
        - order can temporarily be set to NULL while performing moving operations;
        - instance.delete() only deletes the instance, and doesn't shift other instances' orders;
        - some methods are not implemented because they're not used in the codebase;

    Example usage:
        class Step(OrderedModel):
            user = models.ForeignKey(User, on_delete=models.CASCADE)
            order_with_respect_to = ["user_id"]  # steps are ordered per user

            class Meta:
                ordering = ["order"]  # to make queryset ordering correct and consistent
                unique_together = ["user_id", "order"]  # orders are unique per user at the database level

    It's possible for orders to be non-sequential, e.g. order sequence [100, 150, 400] is totally possible and valid.
    """

    order = models.PositiveIntegerField(editable=False, db_index=True, null=True)
    order_with_respect_to: list[str] = []

    class Meta:
        abstract = True
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["order"], name="unique_order"),
        ]

    def save(self, *args, **kwargs) -> None:
        if self.order is None:
            self._save_no_order_provided()
        else:
            super().save()

    @_retry(OperationalError)
    def delete(self, *args, **kwargs) -> None:
        super().delete(*args, **kwargs)

    @_retry((IntegrityError, OperationalError))
    def _save_no_order_provided(self) -> None:
        max_order = self.max_order()
        self.order = max_order + 1 if max_order is not None else 0
        super().save()

    @_retry((IntegrityError, OperationalError))
    def to(self, order: int) -> None:
        if order is None or order < 0:
            raise ValueError("Order must be a positive integer.")

        sql = SQL_TO.format(
            db_table=self._meta.db_table, pk_name=self._meta.pk.name, ordering_condition=self._ordering_condition_sql
        )
        params = {"pk": self.pk, "order": order, **self._ordering_params}

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            self._meta.model.objects.filter(pk=self.pk).update(order=order)

        self.refresh_from_db(fields=["order"])

    def to_index(self, index: int) -> None:
        order = self._get_ordering_queryset().values_list("order", flat=True)[index]
        self.to(order)

    @_retry((IntegrityError, OperationalError))
    def swap(self, order: int) -> None:
        if order is None or order < 0:
            raise ValueError("Order must be a positive integer.")

        sql = SQL_SWAP.format(
            db_table=self._meta.db_table, pk_name=self._meta.pk.name, ordering_condition=self._ordering_condition_sql
        )
        params = {"pk": self.pk, "order": order, **self._ordering_params}

        with transaction.atomic():
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
            self._meta.model.objects.filter(pk=self.pk).update(order=order)

        self.refresh_from_db(fields=["order"])

    def next(self) -> models.Model | None:
        return self._get_ordering_queryset().filter(order__gt=self.order).first()

    def max_order(self) -> int | None:
        return self._get_ordering_queryset().aggregate(models.Max("order"))["order__max"]

    def _get_ordering_queryset(self) -> models.QuerySet:
        return self._meta.model.objects.filter(**self._ordering_params)

    @property
    def _ordering_params(self) -> dict[str, typing.Any]:
        return {field: getattr(self, field) for field in self.order_with_respect_to}

    @property
    def _ordering_condition_sql(self) -> str:
        # This doesn't insert actual values into the query, but rather uses placeholders to avoid SQL injections.
        ordering_parts = ["`t1`.`{0}` = %({0})s".format(field) for field in self.order_with_respect_to]
        return " AND ".join(ordering_parts)
