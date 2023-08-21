import random
import time
import typing
from functools import wraps

from django.db import IntegrityError, OperationalError, models, transaction


def _retry(exc: typing.Type[Exception] | tuple[typing.Type[Exception], ...], max_attempts: int = 5) -> typing.Callable:
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
            self._save_no_order_provided(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    @_retry(OperationalError)  # retry on deadlock
    def delete(self, *args, **kwargs) -> None:
        with transaction.atomic():
            # lock ordering queryset to prevent deleting instances that are used by other transactions
            self._lock_ordering_queryset()
            super().delete(*args, **kwargs)

    @_retry((IntegrityError, OperationalError))  # retry on duplicate order or deadlock
    def _save_no_order_provided(self, *args, **kwargs) -> None:
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
        with transaction.atomic():
            instances = self._lock_ordering_queryset()  # lock ordering queryset to prevent reading inconsistent data
            max_order = max(typing.cast(int, instance.order) for instance in instances) if instances else -1
            self.order = max_order + 1
            super().save(*args, **kwargs)

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

    def _move_instances_to_order(self, instances: list[typing.Self], order: int) -> None:
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

        # Figure out instances that need to be moved and their new orders.
        instances_to_move = []
        if self.order < order:
            for instance in instances:
                if instance.order is not None and self.order < instance.order <= order:
                    instance.order -= 1
                    instances_to_move.append(instance)
        else:
            for instance in instances:
                if instance.order is not None and order <= instance.order < self.order:
                    instance.order += 1
                    instances_to_move.append(instance)

        # If there's nothing to move, just update self.order and return.
        if not instances_to_move:
            self.order = order
            self.save(update_fields=["order"])
            return

        # Temporarily set order values to NULL to avoid unique constraint violations.
        pks = [self.pk] + [instance.pk for instance in instances_to_move]
        self._manager.filter(pk__in=pks).update(order=None)

        # Update orders to appropriate unique values.
        self.order = order
        self._manager.filter(pk__in=pks).bulk_update([self] + instances_to_move, fields=["order"])

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

            # If there's no instance to swap with, just update self.order and return.
            if not other:
                self.order = order
                self.save(update_fields=["order"])
                return

            # Temporarily set order values to NULL to avoid unique constraint violations.
            self._manager.filter(pk__in=[self.pk, other.pk]).update(order=None)

            # Swap order values.
            self.order, other.order = other.order, self.order
            self._manager.filter(pk__in=[self.pk, other.pk]).bulk_update([self, other], fields=["order"])

    def next(self) -> typing.Self | None:
        """
        Return the next instance in the ordering queryset, or None if there's no next instance.
        Example:
            a = OrderedModel(order=1)
            b = OrderedModel(order=2)

            assert a.next() == b
            assert b.next() is None
        """
        return self._get_ordering_queryset().filter(order__gt=self.order).first()

    def max_order(self) -> int | None:
        """
        Return the maximum order value in the ordering queryset or None if there are no instances.
        """
        return self._get_ordering_queryset().aggregate(models.Max("order"))["order__max"]

    @staticmethod
    def _validate_positive_integer(value: int | None) -> None:
        if value is None or not isinstance(value, int) or value < 0:
            raise ValueError("Value must be a positive integer.")

    def _get_ordering_queryset(self) -> models.QuerySet[typing.Self]:
        return self._manager.filter(**self._ordering_params)

    def _lock_ordering_queryset(self) -> list[typing.Self]:
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
