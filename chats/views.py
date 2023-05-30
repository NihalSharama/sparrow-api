import datetime
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .serializers import ConversationSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import serializers
from .models import *
from sparrow.utils import resp_fail, resp_success
from django.db.models import Q
from sparrow.utils import required_data
from .serializers import *
from accounts.models import User
from rest_framework.decorators import action
from rest_framework import status
from sparrow.utils import phone_format
import os
from .models import DeletedConversation
from .utils import get_conv_messages, get_group_messages
# Create your views here.


class ConversationAPI(ModelViewSet):
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        conversation_list = Conversation.objects.filter(
            Q(user1=user) | Q(user2=user))
        return conversation_list

    def create(self, request, *args, **kwargs):
        return Response(resp_fail("Methdod Not Allowed"))

    def list(self, request, *args, **kwargs):
        conversations = self.get_queryset().filter(~Q(archivedBy=request.user))
        groups = GroupChat.objects.filter(
            Q(users=request.user) & ~Q(archivedBy=request.user))

        conversations = ConversationSerializer(conversations,
                                               many=True,
                                               context={
                                                   "request": request
                                               }).data
        groups = GroupChatSerializer(groups, many=True, context={
            "request": request
        }).data

        sorted_convs_groups = sorted(conversations+groups, reverse=True, key=lambda conv: list(
            map(float,
                (conv['last_message']['timestamp'].replace(' ', ':').replace('-', ':').split(':')
                 ) if conv['last_message'] != {} else conv['created_at'].replace('T', ':').replace('-', ':').split(':')
                )))

        return Response(
            resp_success("Conversations Fetched Successfully", {"data": sorted_convs_groups}))

    def retrieve(self, request, pk=None, *args, **kwargs):
        if (not pk):
            return Response(resp_fail("Conversation ID Required.."))

        conv = self.get_queryset().filter(pk=pk)
        if (not conv.exists()):
            return Response(resp_fail("Conversation Does Not Exist..."))
        conv = conv.first()

        user = self.request.user

        class ConvSerializer(serializers.ModelSerializer):
            messages = serializers.SerializerMethodField(
                read_only=True)
            receiver_info = serializers.SerializerMethodField(read_only=True)
            avatar = serializers.SerializerMethodField(read_only=True)

            def get_receiver_info(self, instance):
                receiver_user = None
                current_user = self.context["request"].user
                if (current_user == instance.user1):
                    receiver_user = instance.user2
                else:
                    receiver_user = instance.user1

                data = {
                    "receiver_name":
                    receiver_user.first_name + " " + receiver_user.last_name,
                    "bio":
                    receiver_user.bio,
                    "mobile":
                    receiver_user.mobile
                }
                return data

            def get_avatar(self, instance):
                current_user = request.user
                print(current_user)

                if (current_user == instance.user1):
                    return '/media/' + instance.user2.profile_pic.name
                else:
                    return '/media/' + instance.user1.profile_pic.name

            def get_messages(self, instance):

                messages = get_conv_messages(instance, user)
                return MessageSerializer(messages, many=True).data

            class Meta:
                model = Conversation
                fields = "__all__"

        conv_data = ConvSerializer(conv,
                                   many=False,
                                   context={
                                       "request": request
                                   }).data
        return Response(
            resp_success("Conversation Fetched Successfully.", conv_data))

    def update(self, request, *args, **kwargs):
        return Response(resp_fail("Methdod Not Allowed"))

    def destroy(self, request, pk=None, *args, **kwargs):

        if (pk):
            # queryset = self.get_queryset()
            # convs = queryset.filter(pk=int(pk))
            # if (convs.exists()):
            #     # convs.delete()
            #     conv = convs.first()
            #     deleted_conv, created = DeletedConversation.objects.get_or_create(
            #         user=self.request.user, conv=conv)

            #     if (created):
            #         pass
            #     else:
            #         deleted_conv.deleted_at = datetime.datetime.now()
            #         deleted_conv.save()

            #     return Response(resp_success("Conversation Deleted"))

            # return Response(resp_fail("Conversation Not Found..."))

            queryset = self.get_queryset()
            convs = queryset.filter(pk=int(pk))
            if (convs.exists()):
                convs.delete()
                return Response(resp_success("Conversation Deleted"))

            else:
                return Response(resp_fail("Conversation Not Found..."))
        else:

            return Response(resp_fail("Conversation ID Required."))

    @ action(methods=["POST"], detail=False, url_path="get_available_users")
    def get_available_users(self, request):
        data = request.data
        success, req_data = required_data(data, ["numbers_list"])
        if (not success):

            errors = req_data
            return Response(resp_fail("Invalid Data Provided", data=errors))

        numbers_list, = req_data
        if (type(numbers_list) == list):
            avail_users = []
            for number in numbers_list:
                number_unchanged = number
                formatted = phone_format(number)
                if (not (len(formatted) == 10)):
                    continue

                number = int("".join(formatted.split("-")))

                users = User.objects.filter(mobile=int(number))

                available = users.exists()
                if (available):
                    user = users.first()
                    avail_users.append({
                        "mobile": number_unchanged,
                        "exists": True,
                        "bio": user.bio,
                        "profile_pic": '/media/'+str(user.profile_pic)
                    })

                else:
                    avail_users.append({"mobile": number, "exists": False})

            return Response(
                resp_success("Fetched Available Users", avail_users))

        elif (str(numbers_list).isnumeric()):
            number = numbers_list
            formatted = phone_format(number)
            if (not (len(formatted) == 10)):
                return Response(
                    resp_success("Success",
                                 data=[[]]))

            number = int("".join(formatted.split("-")))

            users = User.objects.filter(mobile=int(number))
            available = users.exists()

            if (available):
                user = users.first()
                return Response(
                    resp_success("Success",
                                 data=[{
                                     "exists": True,
                                     "mobile": numbers_list,
                                     "bio": user.bio,
                                     "profile_pic": '/media/' + str(user.profile_pic)
                                 }]))

            else:
                return Response(
                    resp_success(
                        "Success",
                        data=[{
                            "exists": False,
                            "mobile": numbers_list,
                            #  "profile_pic": user.profile_pic
                        }]))

        else:
            return Response(resp_fail("Invalid Mobile Numbers...."))

    @ action(methods=["POST"], detail=False, url_path="get_conv")
    def get_conv(self, request):

        class ConvSerializer(serializers.ModelSerializer):
            messages = serializers.SerializerMethodField(
                read_only=True)
            receiver_info = serializers.SerializerMethodField(read_only=True)
            avatar = serializers.SerializerMethodField(read_only=True)

            def get_receiver_info(self, instance):
                receiver_user = None
                current_user = self.context["request"].user
                if (current_user == instance.user1):
                    receiver_user = instance.user2
                else:
                    receiver_user = instance.user1

                data = {
                    "receiver_name":
                    receiver_user.first_name + " " + receiver_user.last_name,
                    "bio":
                    receiver_user.bio,
                    "mobile":
                    receiver_user.mobile
                }
                return data

            def get_avatar(self, instance):
                current_user = request.user
                print(current_user)

                if (current_user == instance.user1):
                    return '/media/' + instance.user2.profile_pic.name
                else:
                    return '/media/' + instance.user1.profile_pic.name

            def get_messages(self, instance):

                messages = get_conv_messages(instance, request.user)
                return MessageSerializer(messages, many=True).data

            class Meta:
                model = Conversation
                fields = "__all__"

        data = request.data
        success, req_data = required_data(data, ["mobile"])
        if (not success):
            errors = req_data
            return Response(resp_fail("Invalid Data Provided", data=errors))

        mobile, = req_data
        convs = Conversation.objects.filter(
            Q(user1__mobile=int(mobile)) | Q(user2__mobile=int(mobile)))

        if (convs.exists()):
            conv = convs.first()
            data = ConvSerializer(conv,
                                  many=False,
                                  context={
                                      "request": request
                                  }).data

            return Response(
                resp_success("Conv Fetched...",
                             data={
                                 "exists": True,
                                 "conv": data
                             }))
        return Response(
            resp_success("Response Doesn't Exists...", data={"exists": False}))

    @ action(methods=["POST"], detail=False, url_path="get_group")
    def get_group(self, request):
        class GroupChatSerializer(serializers.ModelSerializer):
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

                messages = get_group_messages(instance, request.user)
                return MessageSerializer(messages, many=True).data

            class Meta:
                model = GroupChat
                fields = "__all__"

        data = request.data
        success, req_data = required_data(data, ["group_id"])
        if (not success):
            errors = req_data
            return Response(resp_fail("Invalid Data Provided", data=errors))

        group_id, = req_data
        groups = GroupChat.objects.filter(id=int(group_id))

        if (groups.exists()):
            group = groups.first()
            data = GroupChatSerializer(group,
                                       many=False,
                                       context={
                                           "request": request
                                       }).data

            return Response(
                resp_success("Group Fetched...",
                             data={
                                 "exists": True,
                                 "group": data
                             }))
        return Response(
            resp_success("Response Doesn't Exists...", data={"exists": False}))

    @ action(methods=["POST"], detail=False, url_path="create_group")
    def create_group(self, request):
        data = request.data
        success, req_data = required_data(
            data, ["mobiles", "admins", "group_name"])
        if (not success):
            return Response(resp_fail("[Mobiles , Admins, Group Name] Required.."))

        mobiles, admins, group_name = req_data

        receivers = []
        grp_admins = []

        # { mobiles, message, admins }

        for mobile in mobiles:
            receiver = User.objects.filter(mobile=mobile)

            if (receiver.exists()):
                reciever = receiver.first()
                receivers.append(reciever)
            else:
                return Response(resp_fail("One Of Reciever Doesn't Exist"))

        for mobile in admins:
            admin = User.objects.filter(mobile=mobile)

            if (admin.exists()):
                admin = admin.first()
                grp_admins.append(admin)
            else:
                return Response(resp_fail("One Of Admin Doesn't Exist"))

        group = GroupChat.objects.create(
            group_name=group_name, created_by=request.user)

        group.users.set(receivers)
        group.admins.set(grp_admins)

        group.save()

        data = GroupChatSerializer(group, many=False, context={
            "request": request}).data
        data["created"] = True
        return Response(resp_success("Group Created", data))

    @action(methods=["POST"], detail=False, url_path="update_group")
    def update_group(self, request, *args, **kwargs):
        data = self.request.data

        if len(data) == 0:
            return resp_fail("No Data Found")

        group = GroupChat.objects.filter(id=data['group_id'])
        if (not group.exists()):
            return Response(
                resp_fail("Group Does Not Exists"))

        group = group.first()
        # if request.user not in group.admins.all():
        #     return Response(
        #         resp_fail("User Is Not Admin"))

        if 'admins' in data:
            admins = []
            for mobile in data['admins']:
                admin = User.objects.filter(mobile=mobile)

                if (admin.exists()):
                    admin = admin.first()
                    admins.append(admin)
                else:
                    return Response(resp_fail("One Of Admin Doesn't Exist"))

            group.admins.set(admins)

        if 'users' in data:
            users = []
            for mobile in data['users']:
                user = User.objects.filter(mobile=mobile)

                if (user.exists()):
                    user = user.first()
                    users.append(user)
                else:
                    return Response(resp_fail("One Of User Doesn't Exist"))

            group.users.set(users)

        group = GroupChatSerializer(
            group, data=data,  partial=True, context={'request': request})

        if group.is_valid():
            group.save()
            new_group = GroupChatSerializerMessages(GroupChat.objects.filter(id=int(data['group_id'])).first(), context={'request': request}
                                                    ).data
            return Response(
                resp_success("Group Updated Succesfully",  new_group))

        return Response(
            resp_fail("Failed To Update Group"))

    @action(methods=["POST"], detail=False, url_path="update_group_profile")
    def update_group_profile(self, request, *args, **kwargs):
        data = self.request.data

        group = GroupChat.objects.filter(id=int(data['group_id']))
        if (not group.exists()):
            return Response(
                resp_fail("Group Does Not Exists"))
        group = group.first()
        if request.user not in group.admins.all():
            return Response(
                resp_fail("User Is Not Admin "))

        class _GroupChatSerializer(serializers.ModelSerializer):
            messages = serializers.SerializerMethodField(read_only=True)
            users = serializers.SerializerMethodField(read_only=True)
            admins = serializers.SerializerMethodField(read_only=True)

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

                messages = get_group_messages(instance, request.user)
                return MessageSerializer(messages, many=True).data

            class Meta:
                model = GroupChat
                fields = "__all__"

        group = _GroupChatSerializer(
            group, data=data, partial=True, context={'request': request})

        # remove old profile pic
        if (group.is_valid()):
            try:
                old_group = _GroupChatSerializer(group, context={'request': request}
                                                 ).data

                if old_group['group_profile'].split('/')[3] != 'default-group.jpg':
                    file_path = old_group['group_profile']
                    os.remove(file_path[1:])
            except Exception:
                resp_fail("Failed To Change Profile",
                          {"errors": group.errors})
            group.save()
            new_group = GroupChatSerializerMessages(GroupChat.objects.filter(id=int(data['group_id'])).first(), context={'request': request}
                                                    ).data

            return Response(
                resp_success("Profile Pic Uploaded Successfully",
                             new_group))
        else:
            return Response(
                resp_fail("Failed To Change Profile Pic",
                          {"errors": group.errors}))

    @action(methods=["POST"], detail=False, url_path="remove_group_profile")
    def remove_group_profile(self, request, *args, **kwargs):
        data = self.request.data

        group = GroupChat.objects.filter(id=int(data['group_id']))
        if (not group.exists()):
            return Response(
                resp_fail("Group Does Not Exists"))
        group = group.first()
        if request.user not in group.admins.all():
            return Response(
                resp_fail("User Is Not Admin "))

        for f in group._meta.fields:
            if f.name == 'group_profile':
                setattr(group, f.name, f.default)

        # remove old profile pic
        try:
            old_group = GroupChatSerializerMessages(group, context={'request': request}
                                                    ).data

            if old_group['group_profile'].split('/')[3] != 'default-group.jpg':
                file_path = old_group['group_profile']
                os.remove(file_path[1:])
        except Exception:
            resp_fail("Failed To Remove Profile",
                      {"errors": group})

        group.save()
        new_group = GroupChatSerializerMessages(GroupChat.objects.filter(id=int(data['group_id'])).first(), context={'request': request}
                                                ).data

        return Response(
            resp_success("Profile Removed Successfully",
                         new_group))

    @action(methods=["POST"], detail=False, url_path="delete_group")
    def delete_group(self, request, *args, **kwargs):
        data = self.request.data
        group = GroupChat.objects.filter(id=int(data['group_id']))

        if group[0].created_by != request.user:
            return Response(
                resp_fail("User Is Not Creator "))

        if (group.exists()):
            group = group.delete()

            return Response(
                resp_success("Group Deleted Successfully"))

        else:
            return Response(
                resp_fail("Group Does Not Exists"))

    @action(methods=["GET"], detail=False, url_path="archived_chats")
    def archived_chats(self, request, *args, **kwargs):
        conversations = self.get_queryset().filter(Q(archivedBy=request.user))
        groups = GroupChat.objects.filter(
            Q(users=request.user) & Q(archivedBy=request.user))

        conversations = ConversationSerializer(conversations,
                                               many=True,
                                               context={
                                                   "request": request
                                               }).data
        groups = GroupChatSerializer(groups, many=True, context={
            "request": request
        }).data

        sorted_convs_groups = sorted(conversations+groups, reverse=True, key=lambda conv: list(
            map(float,
                (conv['last_message']['timestamp'].replace(' ', ':').replace('-', ':').split(':')
                 ) if conv['last_message'] != {} else conv['created_at'].replace('T', ':').replace('-', ':').split(':')
                )))

        return Response(
            resp_success("Archived Chats Fetched Successfully", {"data": sorted_convs_groups}))

    @action(methods=["POST"], detail=False, url_path="archive_unarchive_chat")
    def archive_unarchive_chat(self, request, *args, **kwargs):
        data = request.data

        if 'conv_id' in data:
            chat = Conversation.objects.filter(
                id=int(data['conv_id']))
        elif 'group_id' in data:
            chat = GroupChat.objects.filter(
                id=int(data['group_id']))

        else:
            return Response(
                resp_fail("enter either chat id",
                          {"errors": ''})
            )

        if chat.exists():
            chat = chat.first()

            if data['archive']:
                chat.archivedBy.add(request.user)
            else:
                chat.archivedBy.remove(request.user)

            chat.save()

            return Response(
                resp_success(f"Chat { 'Archived' if data['archive'] else 'Un-Archived' }"))

        else:
            return Response(
                resp_fail("Chat does not exists")
            )


class ChatAPI(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    def get_queryset(self):
        queryset = Message.objects.filter(sender=self.request.user)
        return queryset

    def list(self, request, *args, **kwargs):
        return Response("Method Not Allowed",
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def create(self, request, *args, **kwargs):
        data = request.data
        success, req_data = required_data(
            data, ["mobiles", "message"])
        if (not success):
            return Response(resp_fail("[Mobiles , Message] Required.."))

        mobiles, message = req_data
        user = request.user
        if len(mobiles) == 1:
            receivers = User.objects.filter(mobile=mobiles[0])
            if (receivers.exists()):
                reciever = receivers.first()
            else:
                return Response(resp_fail("Reciever Doesn't Exist"))

            conv = Conversation.objects.filter(
                Q(user1=user, user2=reciever) | Q(user1=reciever, user2=user))

            if (conv.exists()):
                created = False
                conv = conv.first()
            else:
                created = True
                conv = Conversation.objects.create(user1=user, user2=reciever)

            message = Message.objects.create(conversation=conv,
                                             sender=user,
                                             message=message,
                                             replyOf=data['replyof']
                                             )

            message.receivers.set([receivers.first()])
            message.save()

            data = MessageSerializer(message, many=False).data
            data["created"] = created
            return Response(resp_success("Msg Sent...", data))

        else:
            receivers = []

            for mobile in mobiles:
                receiver = User.objects.filter(mobile=mobile)

                if (receiver.exists()):
                    reciever = receiver.first()
                    receivers.append(reciever)
                else:
                    return Response(resp_fail("One Of Reciever Doesn't Exist"))

            group = GroupChat.objects.filter(id=data["group_id"])
            if (group.exists()):
                created = False
                group = group.first()

            message = Message.objects.create(group=group,
                                             sender=user,
                                             message=message,
                                             replyOf=data['replyof']
                                             )

            message.receivers.set(receivers)
            message.save()

            data = MessageSerializer(message, many=False).data
            data["created"] = created
            return Response(resp_success("Msg Sent...", data))

    def update(self, request, *args, **kwargs):
        return Response(
            resp_success("Stared",
                         request.data))

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    @action(methods=["POST"], detail=False, url_path="star_message")
    def star_message(self, request):
        try:
            message = Message.objects.filter(
                id=int(request.data['message_id']))[0]

            message.isStarred = request.data['isStarred']

            message.save()
            message = MessageSerializer(
                message, many=False)

            return Response(
                resp_success("Message Starred",
                             message.data))
        except Exception:
            return Response(
                resp_fail("Failed To Star Message",
                          {"errors": ''})
            )

    @action(methods=["GET"], detail=False, url_path="starred_messages")
    def starred_messages(self, request):
        try:
            messages = Message.objects.filter(
                Q(isStarred=True) & (Q(sender=request.user) | Q(receivers=request.user)))

            messages = MessageSerializer(
                messages, many=True)

            return Response(
                resp_success("Fetched Starred Messages",
                             messages.data))
        except Exception:
            return Response(
                resp_fail("Failed To Star Message",
                          {"errors": ''})
            )

    @action(methods=["POST"], detail=False, url_path="message_status")
    def message_status(self, request):
        try:
            message = Message.objects.filter(
                id=int(request.data['message_id']))[0]

            statusDict = {
                'sent': 0,
                'delivered': 1,
                'seen': 2
            }

            message.status = statusDict[request.data['status']]

            message.save()
            message = MessageSerializer(
                message, many=False)

            return Response(
                resp_success("Message Status Changed",
                             message.data))
        except Exception:
            return Response(
                resp_fail("Failed To Change Message Status",
                          {"errors": ''}))

    @action(methods=["POST"], detail=False, url_path="send_file")
    def send_image(self,  request):
        # request.data["status"] = request.user.id
        if request.data['isImageFile'] == 'true':

            image_form = ImageSerializer(
                data=request.data)
            if (image_form.is_valid()):
                image_form.save()
                return Response(
                    resp_success("Image Send Successfully",
                                 {"data": image_form.data}))
            else:
                return Response(
                    resp_fail("Failed To Send Image",
                              {"errors": image_form.errors}))
        else:
            document_form = DocumentSerializer(
                data=request.data)
            if (document_form.is_valid()):
                document_form.save()
                return Response(
                    resp_success("Document Send Successfully",
                                 {"data": document_form.data}))
            else:
                return Response(
                    resp_fail("Failed To Send Image",
                              {"errors": document_form.errors}))


class CallsAPI(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = MessageSerializer

    @action(methods=["GET"], detail=False, url_path="logs")
    def logs(self, request):
        logs = CallLog.objects.filter(
            participants=request.user).order_by('-created_at')

        logs = CallLogSerializer(
            logs, many=True,  context={'request': request})

        return Response(resp_success('Call Logs Fetched', logs.data))

    @action(methods=["POST"], detail=False, url_path="create_log")
    def create_log(self, request):
        data = request.data

        if 'group_id' in data:
            group_id = int(data['group_id'])
            group = GroupChat.objects.filter(id=group_id)

            if group.exists:
                group = group.first()
                log = CallLog.objects.create(
                    group=group, created_by=request.user)

                log.participants.set(group.users.all())

                log.save()

                data = CallLogSerializer(log, many=False,  context={
                                         'request': request}).data

                return Response(resp_success("Call Log Saved", data))

            else:
                return Response(resp_fail("Group Doesn't Exists"))

        else:
            conv_id = int(data['conv_id'])
            conv = Conversation.objects.filter(id=conv_id)

            if conv.exists:
                conv = conv.first()
                log = CallLog.objects.create(
                    conversation=conv, created_by=request.user)

                log.participants.set([conv.user1, conv.user2])

                log.save()

                data = CallLogSerializer(log, many=False, context={
                                         'request': request}).data

                return Response(resp_success("Call Log Saved", data))

            else:
                return Response(resp_fail("Conv Doesn't Exists"))

    @action(methods=["POST"], detail=False, url_path="remove_log")
    def remove_log(self, request):
        data = request.data

        success, req_data = required_data(
            data, ["log_id"])
        if (not success):
            return Response(resp_fail("[Log Id] Required.."))

        log_id = req_data

        log = CallLog.objects.filter(id=int(log_id[0]))

        if log.exists:
            log = log.first()

            log.participants.remove(request.user)

            log.save()
            return Response(resp_success("Call Log Removed"))
        else:
            return Response(resp_fail("Call Log Doesn't Exists"))

    @action(methods=["DELETE"], detail=False, url_path="remove_all_logs")
    def remove_all_logs(self, request):

        logs = CallLog.objects.filter(participants=request.user)

        if logs.exists:
            for log in logs:

                log.participants.remove(request.user)

                log.save()

            return Response(resp_success("Call Logs Cleared"))
        else:
            return Response(resp_fail("Call Log Doesn't Exists"))
