import factory

from apps.shift_swaps.models import ShiftSwapRequest


class ShiftSwapRequestFactory(factory.DjangoModelFactory):
    class Meta:
        model = ShiftSwapRequest
