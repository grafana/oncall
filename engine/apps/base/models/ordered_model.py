import random
import time
import typing
from functools import wraps

from django.db import IntegrityError, OperationalError, models, transaction
from django.db.models import Case, F, Value, When


def _retry(exc: typing.Type[Exception] | tuple[typing.Type[Exception], ...], max_attempts: int = 15) -> typing.Callable:
    """
    A utility decorator for retrying a function on a given exception(s) up to max_attempts times.
    """

    def _retry_with_params(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            attempts = 0
            while attempts < max_attempts:
                try:
                    return f(*args, **kwargs)
                except exc:
                    if attempts == max_attempts - 1:
                        raise
                    attempts += 1
                    time.sleep(random.random())

        return wrapper

    return _retry_with_params


Self = typing.TypeVar("Self", bound="OrderedModel")


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

    @_retry(OperationalError)  # retry on deadlock
    def delete(self, *args, **kwargs) -> None:
        super().delete(*args, **kwargs)

    @_retry((IntegrityError, OperationalError))
    def _save_no_order_provided(self) -> None:
        """
        Save self to DB without an order provided (e.g on creation).
        Order is set to the next available order, or 0 if there are no other instances.
        Example:
            a = OrderedModel.objects.create()
            b = OrderedModel.objects.create()
            c = OrderedModel.objects.create(order=10)
            d = OrderedModel.objects.create()

            assert (a.order, b.order, c.order, d.order) == (0, 1, 10, 11)
        """
        max_order = self.max_order()
        self.order = max_order + 1 if max_order is not None else 0
        super().save()

    @_retry(OperationalError)  # retry on deadlock
    def to(self, order: int) -> None:
        """
        Move self to a given order, adjusting other instances' orders if necessary.
        Example:
            a = OrderedModel(order=1)
            b = OrderedModel(order=2)
            c = OrderedModel(order=3)

            a.to(3)  # move the first element to the last order
            assert (a.order, b.order, c.order) == (3, 1, 2)  # [a, b, c] -> [b, c, a]
        """
        self._validate_positive_integer(order)
        with transaction.atomic():
            instances = self._lock_ordering_queryset()
            self._move_instances_to_order(instances, order)

    @_retry(OperationalError)  # retry on deadlock
    def to_index(self, index: int) -> None:
        """
        Move self to a given index, adjusting other instances' orders if necessary.
        Similar with to(), but accepts an index instead of an order.
        This might be handy as orders might be non-sequential, but most clients assume that they are sequential.

        Example:
            a = OrderedModel(order=1)
            b = OrderedModel(order=5)
            c = OrderedModel(order=10)

            a.to_index(2)  # move the first element to the second index (where c is)
            assert (a.order, b.order, c.order) == (10, 4, 9)  # [a, b, c] -> [b, c, a]
        """
        self._validate_positive_integer(index)
        with transaction.atomic():
            instances = self._lock_ordering_queryset()
            order = instances[index].order  # get order of the instance at the given index
            self._move_instances_to_order(instances, order)

    def _move_instances_to_order(self, instances: list[Self], order: int) -> None:
        """
        Helper method for moving self to a given order, adjusting other instances' orders if necessary.
        Must be called within a transaction that locks the ordering queryset.
        """

        # Get the up-to-date instance from the database, because it might have been updated by another transaction.
        try:
            _self = next(instance for instance in instances if instance.pk == self.pk)
            self.order = _self.order
            assert self.order is not None
        except StopIteration:
            raise self.DoesNotExist()

        # If the order is already correct, do nothing.
        if self.order == order:
            return

        # Figure out instances that need to be moved.
        if self.order < order:
            instances_to_move = [
                instance
                for instance in instances
                if instance.order is not None and self.order < instance.order <= order
            ]
        else:
            instances_to_move = [
                instance
                for instance in instances
                if instance.order is not None and order <= instance.order < self.order
            ]

        # Temporarily set self.order to NULL and update other instances' orders in a single SQL command.
        if instances_to_move:
            order_by = "order" if self.order < order else "-order"
            order_delta = -1 if self.order < order else 1
            self._manager.filter(pk__in=[self.pk] + [instance.pk for instance in instances_to_move]).order_by(
                order_by
            ).update(
                order=Case(
                    When(pk=self.pk, then=Value(None)),
                    default=F("order") + order_delta,
                )
            )

        # Update self.order from NULL to the correct value.
        self.order = order
        self.save(update_fields=["order"])

    @_retry(OperationalError)  # retry on deadlock
    def swap(self, order: int) -> None:
        """
        Swap self with an instance at a given order.
        Example:
            a = OrderedModel(order=1)
            b = OrderedModel(order=2)
            c = OrderedModel(order=3)
            d = OrderedModel(order=4)

            a.swap(4)  # swap the first element with the last element
            assert (a.order, b.order, c.order, d.order) == (4, 2, 3, 1)  # [a, b, c, d] -> [d, b, c, a]
        """
        self._validate_positive_integer(order)
        with transaction.atomic():
            instances = self._lock_ordering_queryset()

            # Get the up-to-date instance from the database, because it might have been updated by another transaction.
            try:
                _self = next(instance for instance in instances if instance.pk == self.pk)
                self.order = _self.order
                assert self.order is not None
            except StopIteration:
                raise self.DoesNotExist()

            # If the order is already correct, do nothing.
            if self.order == order:
                return

            # Get the instance to swap with.
            try:
                other = next(instance for instance in instances if instance.order == order)
            except StopIteration:
                other = None

            # Temporarily set self.order to NULL and update the other instance's order in a single SQL command.
            if other:
                order_by = "order" if self.order < order else "-order"
                self._manager.filter(pk__in=[self.pk, other.pk]).order_by(order_by).update(
                    order=Case(
                        When(pk=self.pk, then=Value(None)),
                        default=Value(self.order),
                    )
                )

            # Update self.order from NULL to the correct value.
            self.order = order
            self.save(update_fields=["order"])

    def next(self) -> Self | None:
        return self._get_ordering_queryset().filter(order__gt=self.order).first()

    def max_order(self) -> int | None:
        return self._get_ordering_queryset().aggregate(models.Max("order"))["order__max"]

    @staticmethod
    def _validate_positive_integer(value: int | None) -> None:
        if value is None or not isinstance(value, int) or value < 0:
            raise ValueError("Value must be a positive integer.")

    def _get_ordering_queryset(self) -> models.QuerySet[Self]:
        return self._manager.filter(**self._ordering_params)

    def _lock_ordering_queryset(self) -> list[Self]:
        """
        Locks the ordering queryset with SELECT FOR UPDATE and returns the queryset as a list.
        This allows to prevent concurrent updates from different transactions.
        """
        return list(self._get_ordering_queryset().select_for_update().only("pk", "order"))

    @property
    def _manager(self):
        return self._meta.default_manager

    @property
    def _ordering_params(self) -> dict[str, typing.Any]:
        return {field: getattr(self, field) for field in self.order_with_respect_to}
