import random
import threading

import pytest
from django.db import models

from common.ordered_model.ordered_model import OrderedModel


class TestOrderedModel(OrderedModel):
    __test__ = False

    test_field = models.CharField(max_length=255)
    extra_field = models.IntegerField(null=True, default=None)
    order_with_respect_to = ["test_field"]

    class Meta:
        app_label = "base"
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["test_field", "order"], name="unique_test_field_order"),
        ]


def _get_ids():
    return list(TestOrderedModel.objects.filter(test_field="test").values_list("id", flat=True))


def _get_orders():
    return list(TestOrderedModel.objects.filter(test_field="test").values_list("order", flat=True))


def _orders_are_sequential():
    orders = _get_orders()
    return orders == list(range(len(orders)))


@pytest.mark.django_db
def test_ordered_model_create():
    first = TestOrderedModel.objects.create(test_field="test")
    second = TestOrderedModel.objects.create(test_field="test")

    assert first.order == 0
    assert second.order == 1


@pytest.mark.django_db
def test_ordered_model_delete():
    instances = [TestOrderedModel.objects.create(test_field="test") for _ in range(3)]

    instances[1].delete()
    assert instances[1].pk is None
    assert _get_ids() == [instances[0].id, instances[2].id]
    assert _get_orders() == [0, 2]


@pytest.mark.django_db
def test_ordered_model_to():
    instances = [TestOrderedModel.objects.create(test_field="test") for _ in range(5)]

    def _ids(indices):
        return [instances[i].id for i in indices]

    # move to the end
    instances[0].to(4)
    assert instances[0].order == 4
    assert _get_ids() == _ids([1, 2, 3, 4, 0])
    assert _orders_are_sequential()

    # move to the beginning
    instances[0].to(0)
    assert instances[0].order == 0
    assert _get_ids() == _ids([0, 1, 2, 3, 4])
    assert _orders_are_sequential()

    # move to the middle
    instances[0].to(2)
    assert instances[0].order == 2
    assert _get_ids() == _ids([1, 2, 0, 3, 4])
    assert _orders_are_sequential()

    # move from the middle to the end
    instances[0].to(4)
    assert instances[0].order == 4
    assert _get_ids() == _ids([1, 2, 3, 4, 0])
    assert _orders_are_sequential()

    # move from the end to the second position
    instances[0].to(1)
    assert instances[0].order == 1
    assert _get_ids() == _ids([1, 0, 2, 3, 4])
    assert _orders_are_sequential()

    # move from the second position to the beginning
    instances[0].to(0)
    assert instances[0].order == 0
    assert _get_ids() == _ids([0, 1, 2, 3, 4])
    assert _orders_are_sequential()

    # don't move if the order is the same
    for instance in instances:
        instance.to(instance.order)
        assert instance.order == instance.order
        assert _get_ids() == _ids([0, 1, 2, 3, 4])
        assert _orders_are_sequential()


@pytest.mark.django_db
def test_ordered_model_to_index():
    instances = [TestOrderedModel.objects.create(test_field="test") for _ in range(5)]

    def _ids(indices):
        return [instances[i].id for i in indices]

    # move to the end
    instances[0].to_index(4)
    assert instances[0].order == 4
    assert _get_ids() == _ids([1, 2, 3, 4, 0])
    assert _orders_are_sequential()

    # move to the beginning
    instances[0].to_index(0)
    assert instances[0].order == 0
    assert _get_ids() == _ids([0, 1, 2, 3, 4])
    assert _orders_are_sequential()

    # move to the middle
    instances[0].to_index(2)
    assert instances[0].order == 2
    assert _get_ids() == _ids([1, 2, 0, 3, 4])
    assert _orders_are_sequential()

    # move from the middle to the end
    instances[0].to_index(4)
    assert instances[0].order == 4
    assert _get_ids() == _ids([1, 2, 3, 4, 0])
    assert _orders_are_sequential()

    # move from the end to the second position
    instances[0].to_index(1)
    assert instances[0].order == 1
    assert _get_ids() == _ids([1, 0, 2, 3, 4])
    assert _orders_are_sequential()

    # move from the second position to the beginning
    instances[0].to_index(0)
    assert instances[0].order == 0
    assert _get_ids() == _ids([0, 1, 2, 3, 4])
    assert _orders_are_sequential()

    # don't move if the order is the same
    for instance in instances:
        instance.to_index(instance.order)
        assert instance.order == instance.order
        assert _get_ids() == _ids([0, 1, 2, 3, 4])
        assert _orders_are_sequential()


@pytest.mark.django_db
def test_ordered_model_swap():
    instances = [TestOrderedModel.objects.create(test_field="test") for _ in range(5)]

    def _ids(indices):
        return [instances[i].id for i in indices]

    # swap with last
    instances[0].swap(4)
    assert instances[0].order == 4
    assert _get_ids() == _ids([4, 1, 2, 3, 0])
    assert _orders_are_sequential()

    # swap with first
    instances[0].swap(0)
    assert instances[0].order == 0
    assert _get_ids() == _ids([0, 1, 2, 3, 4])
    assert _orders_are_sequential()

    # swap with middle
    instances[0].swap(2)
    assert instances[0].order == 2
    assert _get_ids() == _ids([2, 1, 0, 3, 4])
    assert _orders_are_sequential()

    # swap from the middle to the end
    instances[0].swap(4)
    assert instances[0].order == 4
    assert _get_ids() == _ids([2, 1, 4, 3, 0])
    assert _orders_are_sequential()

    # swap from the end to the second position
    instances[0].swap(1)
    assert instances[0].order == 1
    assert _get_ids() == _ids([2, 0, 4, 3, 1])
    assert _orders_are_sequential()

    # swap from the second position to the beginning
    instances[0].swap(0)
    assert instances[0].order == 0
    assert _get_ids() == _ids([0, 2, 4, 3, 1])
    assert _orders_are_sequential()

    # swap with itself
    for instance in instances:
        instance.refresh_from_db(fields=["order"])
        instance.swap(instance.order)
        assert instance.order == instance.order
        assert _get_ids() == _ids([0, 2, 4, 3, 1])
        assert _orders_are_sequential()


@pytest.mark.django_db
def test_order_with_respect_to_isolation():
    instances = [TestOrderedModel.objects.create(test_field="test") for _ in range(5)]
    other_instances = [TestOrderedModel.objects.create(test_field="test1") for _ in range(5)]

    assert [i.order for i in instances] == [0, 1, 2, 3, 4]
    assert [i.order for i in other_instances] == [0, 1, 2, 3, 4]

    assert instances[-1].next() is None
    assert instances[-1].max_order() == 4

    instances[0].to(8)
    instances[1].swap(7)

    for idx, instance in enumerate(other_instances):
        instance.refresh_from_db()
        assert instance.order == idx

    with pytest.raises(IndexError):
        instances[0].to_index(6)


# Tests below are for checking that concurrent operations are performed correctly.
# They are skipped by default because they might take a lot of time to run.
# It could be useful to run them manually when making changes to the code, making sure
# that the changes don't break concurrent operations. To run the tests, set SKIP_CONCURRENT to False.
SKIP_CONCURRENT = True


@pytest.mark.skipif(SKIP_CONCURRENT, reason="OrderedModel concurrent tests are skipped to speed up tests")
@pytest.mark.django_db(transaction=True)
def test_ordered_model_create_concurrent():
    LOOPS = 30
    THREADS = 10
    exceptions = []

    def create():
        for loop in range(LOOPS):
            try:
                TestOrderedModel.objects.create(test_field="test")
            except Exception as e:
                exceptions.append(e)

    threads = [threading.Thread(target=create) for _ in range(THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not exceptions
    assert TestOrderedModel.objects.count() == LOOPS * THREADS
    assert _orders_are_sequential()


@pytest.mark.skipif(SKIP_CONCURRENT, reason="OrderedModel concurrent tests are skipped to speed up tests")
@pytest.mark.django_db(transaction=True)
def test_ordered_model_to_concurrent():
    THREADS = 300
    exceptions = []

    TestOrderedModel.objects.all().delete()  # clear table
    instances = [TestOrderedModel.objects.create(test_field="test") for _ in range(THREADS)]

    random.seed(42)
    positions = [random.randint(0, THREADS - 1) for _ in range(THREADS)]

    def to(idx):
        try:
            instance = instances[idx]
            instance.to(positions[idx])  # swap with next
        except Exception as e:
            exceptions.append(e)

    threads = [threading.Thread(target=to, args=(idx,)) for idx in range(THREADS - 1)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # can only check that orders are still sequential and that there are no exceptions
    # can't check the exact order because it changes depending on the order of execution
    assert not exceptions
    assert _orders_are_sequential()


@pytest.mark.skipif(SKIP_CONCURRENT, reason="OrderedModel concurrent tests are skipped to speed up tests")
@pytest.mark.django_db(transaction=True)
def test_ordered_model_swap_concurrent():
    THREADS = 300
    exceptions = []

    TestOrderedModel.objects.all().delete()  # clear table
    instances = [TestOrderedModel.objects.create(test_field="test") for _ in range(THREADS)]

    # generate random unique orders
    random.seed(42)
    unique_orders = list(range(THREADS))
    random.shuffle(unique_orders)

    def swap(idx):
        try:
            instance = instances[idx]
            instance.swap(unique_orders[idx])
        except Exception as e:
            exceptions.append(e)

    threads = [threading.Thread(target=swap, args=(idx,)) for idx in range(THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not exceptions
    assert _orders_are_sequential()

    # in case of unique orders, the final order is deterministic
    assert list(TestOrderedModel.objects.order_by("id").values_list("order", flat=True)) == unique_orders


@pytest.mark.skipif(SKIP_CONCURRENT, reason="OrderedModel concurrent tests are skipped to speed up tests")
@pytest.mark.django_db(transaction=True)
def test_ordered_model_swap_non_unique_orders_concurrent():
    THREADS = 300
    exceptions = []

    TestOrderedModel.objects.all().delete()  # clear table
    instances = [TestOrderedModel.objects.create(test_field="test") for _ in range(THREADS)]

    # generate random non-unique orders
    random.seed(42)
    positions = [random.randint(0, THREADS - 1) for _ in range(THREADS)]

    def swap(idx):
        try:
            instance = instances[idx]
            instance.swap(positions[idx])
        except Exception as e:
            exceptions.append(e)

    threads = [threading.Thread(target=swap, args=(idx,)) for idx in range(THREADS)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    # can only check that orders are still sequential and that there are no exceptions
    # can't check the exact order because it changes depending on the order of execution
    assert not exceptions
    assert _orders_are_sequential()


@pytest.mark.skipif(SKIP_CONCURRENT, reason="OrderedModel concurrent tests are skipped to speed up tests")
@pytest.mark.django_db(transaction=True)
def test_ordered_model_create_swap_and_delete_concurrent():
    """Check that create+swap, swap and delete operations are performed correctly when run concurrently."""

    THREADS = 100
    exceptions = []

    instances = [TestOrderedModel.objects.create(test_field="test", extra_field=idx) for idx in range(THREADS * 3)]

    def create_swap(idx):
        try:
            instance = TestOrderedModel.objects.create(test_field="test", extra_field=idx + 1000)
            instance.swap(idx)
        except Exception as e:
            exceptions.append(("create_swap", e))

    def swap(idx):
        try:
            instances[idx].swap(idx + 1)
        except Exception as e:
            exceptions.append(("swap", e))

    def delete(idx):
        try:
            instances[idx].delete()
        except Exception as e:
            exceptions.append(("delete", e))

    threads = [threading.Thread(target=create_swap, args=(idx,)) for idx in list(range(THREADS))]
    threads += [threading.Thread(target=delete, args=(idx,)) for idx in range(THREADS)]
    threads += [threading.Thread(target=swap, args=(idx,)) for idx in range(THREADS, THREADS * 2 - 1)]

    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    expected_extra_field_values = list(range(1000, 1000 + THREADS))
    expected_extra_field_values += [THREADS * 2 - 1] + list(range(THREADS, THREADS * 2 - 1))
    expected_extra_field_values += [instance.extra_field for instance in instances[THREADS * 2 : THREADS * 3]]

    assert not exceptions
    assert _orders_are_sequential()
    assert list(TestOrderedModel.objects.values_list("extra_field", flat=True)) == expected_extra_field_values
