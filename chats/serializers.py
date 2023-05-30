from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from .models import *
from .utils import get_conv_messages, get_group_messages


class MessageSerializer(ModelSerializer):

    status = serializers.SerializerMethodField(read_only=True)
    document = serializers.SerializerMethodField(read_only=True)
    sender = serializers.SerializerMethodField(read_only=True)
    sender_id = serializers.SerializerMethodField(read_only=True)

    def get_status(self, instance):

        msg_status = instance.status
        status_text = ''
        if (msg_status == 0):
            status_text = "sent"
        elif msg_status == 1:
            msg_status = "delivered"
        elif msg_status == 2:
            status_text = "seen"

        return status_text

    def get_document(self, instance):
        image = Image.objects.filter(message=instance.id)
        doc = Document.objects.filter(message=instance.id)

        if image.exists():
            image = ImageSerializer(image[0]).data
            return image
        elif doc.exists():
            doc = DocumentSerializer(doc[0]).data
            return doc
        else:
            return

    def get_sender(self, instance):
        return instance.sender.mobile

    def get_sender_id(self, instance):
        return instance.sender.id

    class Meta:
        model = Message
        fields = "__all__"


class ConversationSerializer(ModelSerializer):
    conv_name = serializers.SerializerMethodField(read_only=True)
    conv_mobile = serializers.SerializerMethodField(read_only=True)
    last_message = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.SerializerMethodField(read_only=True)

    def get_conv_mobile(self, instance):
        current_user = self.context["request"].user
        print(current_user)
        if (current_user == instance.user1):
            return instance.user2.mobile
        else:
            return instance.user1.mobile

    def get_conv_name(self, instance):
        current_user = self.context["request"].user
        print(current_user)
        if (current_user == instance.user1):
            return instance.user2.first_name
        else:
            return instance.user1.first_name

    def get_avatar(self, instance):
        current_user = self.context["request"].user
        print(current_user)

        if (current_user == instance.user1):
            return '/media/' + instance.user2.profile_pic.name
        else:
            return '/media/' + instance.user1.profile_pic.name

    def get_last_message(self, instance):
        current_user = self.context["request"].user
        messages = get_conv_messages(instance, current_user)
        if (messages.exists()):
            last_message = messages.order_by("-created_at").first()
            msg_status = last_message.status
            msg_time = "{:s} {:s}".format(
                str(last_message.created_at.date()), str(last_message.created_at.time()))

            status_text = ''
            if (msg_status == 0):
                status_text = "sent"
            elif msg_status == 1:
                msg_status = "delivered"
            elif msg_status == 2:
                status_text = "seen"

            return {
                "message": last_message.message,
                "status": status_text,
                "timestamp": msg_time,
                "sender": last_message.sender.id
            }
        else:
            return {}

    class Meta:
        model = Conversation
        fields = "__all__"


class ImageSerializer(ModelSerializer):

    class Meta:
        model = Image
        fields = "__all__"


class DocumentSerializer(ModelSerializer):

    class Meta:
        model = Document
        fields = "__all__"


class GroupChatSerializer(ModelSerializer):
    last_message = serializers.SerializerMethodField(read_only=True)
    group_profile = serializers.SerializerMethodField(read_only=True)
    users = serializers.SerializerMethodField(read_only=True)
    admins = serializers.SerializerMethodField(read_only=True)

    def get_last_message(self, instance):
        current_user = self.context["request"].user
        messages = get_group_messages(instance, current_user)

        if (messages.exists()):
            last_message = messages.order_by("-created_at").first()
            msg_status = last_message.status
            msg_time = "{:s} {:s}".format(
                str(last_message.created_at.date()), str(last_message.created_at.time()))

            status_text = ''
            if (msg_status == 0):
                status_text = "sent"
            elif msg_status == 1:
                msg_status = "delivered"
            elif msg_status == 2:
                status_text = "seen"

            return {
                "message": last_message.message,
                "status": status_text,
                "timestamp": msg_time,
                "sender": last_message.sender.id
            }
        else:
            return {}

    def get_group_profile(self, instance):
        return '/media/' + instance.group_profile.name

    def get_users(self, instance):
        users_mobile = []
        for user in instance.users.all():
            users_mobile.append(user.mobile)
        return users_mobile

    def get_admins(self, instance):
        admins_mobile = []
        for admin in instance.admins.all():
            admins_mobile.append(admin.mobile)
        return admins_mobile

    class Meta:
        model = GroupChat
        fields = "__all__"


class GroupChatSerializerMessages(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField(read_only=True)
    group_profile = serializers.SerializerMethodField(read_only=True)
    users = serializers.SerializerMethodField(read_only=True)
    admins = serializers.SerializerMethodField(read_only=True)

    def get_group_profile(self, instance):
        return '/media/' + instance.group_profile.name

    def get_users(self, instance):
        users_mobile = []

        for user in instance.users.all():
            users_mobile.append(user.mobile)
        return users_mobile

    def get_admins(self, instance):
        admins_mobile = []
        for admin in instance.admins.all():
            admins_mobile.append(admin.mobile)
        return admins_mobile

    def get_messages(self, instance):

        messages = get_group_messages(instance, self.context["request"].user)
        return MessageSerializer(messages, many=True).data

    class Meta:
        model = GroupChat
        fields = "__all__"


class CallLogSerializer(serializers.ModelSerializer):

    group = serializers.SerializerMethodField(read_only=True)
    conversation = serializers.SerializerMethodField(read_only=True)
    avatar = serializers.SerializerMethodField(read_only=True)

    def get_group(self, instance):
        if instance.group:
            return instance.group.group_name
        else:
            return

    def get_conversation(self, instance):
        if instance.conversation:
            current_user = self.context["request"].user

            if (current_user == instance.conversation.user1):
                return instance.conversation.user2.mobile
            else:
                return instance.conversation.user1.mobile
        else:
            return

    def get_avatar(self, instance):
        if instance.group:
            return '/media/' + instance.group.group_profile.name
        else:
            current_user = self.context["request"].user

            if (current_user == instance.conversation.user1):
                return '/media/' + instance.conversation.user2.profile_pic.name
            else:
                return '/media/' + instance.conversation.user1.profile_pic.name

    class Meta:
        model = CallLog
        fields = "__all__"
