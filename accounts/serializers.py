from .models import User
from rest_framework.serializers import ModelSerializer
from django.db.models.fields import NOT_PROVIDED
from rest_framework import serializers


class UserSerializer(ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
