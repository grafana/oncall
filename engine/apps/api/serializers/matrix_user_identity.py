from rest_framework import serializers

from apps.matrix.models import MatrixUserIdentity


class MatrixUserIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = MatrixUserIdentity
        fields = '__all__'
