from rest_framework import serializers

from common.api_helpers.exceptions import BadRequest


class OrderedModelSerializer(serializers.ModelSerializer):
    """Ordered model serializer to be used in public API."""

    position = serializers.IntegerField(required=False, source="order")
    # manual_order=True is intended for use by Terraform provider only, and is not a documented feature.
    manual_order = serializers.BooleanField(default=False, write_only=True)

    class Meta:
        fields = ["position", "manual_order"]

    def create(self, validated_data):
        # Remove "manual_order" and "order" fields from validated_data, so they are not passed to create method.
        manual_order = validated_data.pop("manual_order", False)
        order = validated_data.pop("order", None)

        # Create the instance.
        # Instances are always created at the end of the list, and then moved to the desired position by _adjust_order.
        instance = super().create(validated_data)

        # Adjust order of the instance if necessary.
        if order is not None:
            self._adjust_order(instance, manual_order, order, created=True)

        return instance

    def update(self, instance, validated_data):
        # Remove "manual_order" and "order" fields from validated_data, so they are not passed to update method.
        manual_order = validated_data.pop("manual_order", False)
        order = validated_data.pop("order", None)

        # Adjust order of the instance if necessary.
        if order is not None:
            self._adjust_order(instance, manual_order, order, created=False)

        # Proceed with the update.
        return super().update(instance, validated_data)

    @staticmethod
    def _adjust_order(instance, manual_order, order, created):
        # Passing order=-1 means that the policy should be moved to the end of the list.
        # Works only for public API but not for Terraform provider.
        if order == -1 and not manual_order:
            if created:
                # The policy was just created, so it is already at the end of the list.
                return

            order = instance.max_order()
            # max_order() can't be None here because at least one instance exists – the one we are moving.
            assert order is not None

        # Check the order is in the valid range.
        # https://docs.djangoproject.com/en/4.1/ref/models/fields/#positiveintegerfield
        if order < 0 or order > 2147483647:
            raise BadRequest(detail="Invalid value for position field")

        # Orders are swapped instead of moved when using Terraform, because Terraform may issue concurrent requests
        # to create / update / delete multiple policies. "Move to" operation is not deterministic in this case, and
        # final order of policies may be different depending on the order in which requests are processed. On the other
        # hand, the result of concurrent "swap" operations is deterministic and does not depend on the order in
        # which requests are processed.
        if manual_order:
            instance.swap(order)
        else:
            instance.to(order)
