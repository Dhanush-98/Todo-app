from rest_framework import serializers
from api.models import Todo


class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at", "user"]

    def validate(self, attrs):
        attrs["user"] = self.context["request"].user
        return attrs
