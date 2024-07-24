from rest_framework import serializers
from rest_framework.utils import model_meta

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

    def _update(self, instance, validated_data):
        # customize the update method to make sure order field is not saved again
        # (which could trigger an integrity error if there was another concurrent update changing order)
        serializers.raise_errors_on_nested_writes("update", self, validated_data)
        info = model_meta.get_field_info(instance)

        # Simply set each attribute on the instance, and then save it.
        # Note that unlike `.create()` we don't need to treat many-to-many
        # relationships as being a special case. During updates we already
        # have an instance pk for the relationships to be associated with.
        m2m_fields = []
        update_fields = []
        for attr, value in validated_data.items():
            if attr in info.relations and info.relations[attr].to_many:
                m2m_fields.append((attr, value))
            else:
                setattr(instance, attr, value)
                update_fields.append(attr)

        # NOTE: this is the only difference, update changed fields to avoid saving order field again
        if update_fields:
            instance.save(update_fields=update_fields)

        # Note that many-to-many fields are set after updating instance.
        # Setting m2m fields triggers signals which could potentially change
        # updated instance and we do not want it to collide with .update()
        for attr, value in m2m_fields:
            field = getattr(instance, attr)
            field.set(value)

        return instance

    def update(self, instance, validated_data):
        # Remove "manual_order" and "order" fields from validated_data, so they are not passed to update method.
        manual_order = validated_data.pop("manual_order", False)
        order = validated_data.pop("order", None)

        # Adjust order of the instance if necessary.
        if order is not None:
            self._adjust_order(instance, manual_order, order, created=False)

        # Proceed with the update.
        return self._update(instance, validated_data)

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
