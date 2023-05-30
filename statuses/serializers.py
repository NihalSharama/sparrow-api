from rest_framework.serializers import ModelSerializer
from .models import Status
from accounts.serializers import UserSerializer
from rest_framework import serializers


class StatusSerializer(ModelSerializer):

    user_mobile = serializers.SerializerMethodField(read_only=True)
    user_profile = serializers.SerializerMethodField(read_only=True)
    views = serializers.SerializerMethodField(read_only=True)

    def get_user_mobile(self, instance):
        if ('status_info' not in self.context):
            return ''

        status_info = self.context['status_info']
        return status_info.user.mobile

    def get_user_profile(self, instance):
        if ('status_info' not in self.context):
            return ''

        status_info = self.context['status_info']
        return '/media/' + status_info.user.profile_pic.name

    def get_views(self, instance):

        viewers = instance.views.all()
        viewers_details = []

        for viewer in viewers:
            user = UserSerializer(viewer, many=False).data
            viewers_details.append({
                "id": user['id'],
                "first_name": user['first_name'],
                "last_name": user['last_name'],
                "mobile": user['mobile'],
                "profile_pic": user['profile_pic']
            })

        return viewers_details

    class Meta:
        model = Status
        fields = "__all__"
