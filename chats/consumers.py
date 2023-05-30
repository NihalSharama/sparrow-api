from channels.generic.websocket import AsyncJsonWebsocketConsumer, WebsocketConsumer
import json
from sparrow.utils import get_model
from accounts.models import User
from .models import WSClient, SignallingWSClient
from channels.db import database_sync_to_async
from .websocket_constants import *
from .middleware import get_user
from jwt import decode as jwt_decode
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import UntypedToken
from django.conf import settings
from asgiref.sync import async_to_sync
from .ws_permissions import wsIsAuthenticated


class ChatChannel(AsyncJsonWebsocketConsumer):

    async def connect(self):
        # Adding User to Channel
        self.user = self.scope["user"]
        isAuth = wsIsAuthenticated(self)

        if (not isAuth):
            await self.close()
            return

        await self.clean_user()
        await self.add_user()
        await self.accept()

    async def disconnect(self, code):
        isAuth = wsIsAuthenticated(self)
        print('close' + str(isAuth))
        if (not isAuth):
            pass
        else:
            await self.clean_user()

    async def receive(self, text_data='', bytes_data=None, **kwargs):
        data = json.loads(text_data)

        receivers_mobile = data["receivers_mobile"]

        for receiver_mobile in receivers_mobile:
            event_type = data["event_type"]
            receiver_channel_name = await self.get_channel(receiver_mobile)

            if (receiver_channel_name):
                await self.channel_layer.send(receiver_channel_name, {
                    "type": event_type,
                    "payload": text_data
                })

                if (event_type == CHAT_STATUS):
                    await self.send(json.dumps({"status": "online", "event_type": "chat.status"}))
                elif (event_type == SDP_RECEIVE):
                    await self.send(json.dumps({"status": "online", "event_type": "chat.status"}))
            else:
                print("Hey")
                if (event_type == CHAT_STATUS):
                    await self.send(json.dumps({"status": "offline", "event_type": "chat.status"}))
                if (event_type == SDP_RECEIVE):
                    await self.send(json.dumps({"status": "offline", "event_type": "chat.status"}))

    async def chat_receive(self, text_data):
        data = text_data['payload']
        data = json.loads(data)
        data["event_type"] = CHAT_RECEIVE
        await self.send(json.dumps(data))

    async def group_chat_receive(self, text_data):
        data = text_data['payload']
        data = json.loads(data)
        data["event_type"] = GROUP_CHAT_RECEIVE
        await self.send(json.dumps(data))

    async def sdp_receive(self, text_data):
        data = text_data["payload"]
        data = json.loads(data)
        data["event_type"] = SDP_RECEIVE
        await self.send(json.dumps(data))

    async def chat_status(self, text_data):
        data = text_data["payload"]
        data = json.loads(data)
        data["event_type"] = CHAT_STATUS
        await self.send(json.dumps(data))

    async def message_status(self, text_data):
        data = text_data["payload"]
        data = json.loads(data)
        data["event_type"] = MESSAGE_STATUS
        await self.send(json.dumps(data))

    async def message_delete(self, text_data):
        data = text_data["payload"]
        data = json.loads(data)
        data["event_type"] = MESSAGE_DELETE
        await self.send(json.dumps(data))

    async def message_star(self, text_data):
        data = text_data["payload"]
        data = json.loads(data)
        data["event_type"] = MESSAGE_STAR
        await self.send(json.dumps(data))

    @database_sync_to_async
    def get_channel(self, mobile):
        channels = WSClient.objects.filter(user__mobile=int(mobile))
        if (channels.exists()):
            channel_name = channels.last().channel_name
            return channel_name
        else:
            return None

    @database_sync_to_async
    def get_user_channel(self, to_user_id):
        to_user = get_model(User, id=int(to_user_id))
        if (not to_user["exist"]):
            return False, "The User Does Not Exist"

        to_user = to_user['data']
        active_to_user = WSClient.objects.filter(user__id=int(to_user_id))
        return active_to_user.channel_name, active_to_user.user

    @database_sync_to_async
    def add_user(self):
        self.clean_user()
        # adding user to groups
        # for group in self.user.group.all():
        #     async_to_sync(self.channel_layer.group_add)(
        #         str(group.id), self.channel_name
        #     )

        WSClient.objects.create(user=self.user, channel_name=self.channel_name)

    @database_sync_to_async
    def clean_user(self):
        print("Cleaned")
        for group in self.user.group.all():
            async_to_sync(self.channel_layer.group_discard)(
                str(group.id), self.channel_name
            )

        WSClient.objects.filter(user=self.user).delete()


# Signalling Constants
OFFER = "rtc.offer"
ANSWER = "rtc.answer"
CANDIDATE = "rtc.candidate"
REMOTE = "rtc.remote"  # when remote config change (video on/ff)
GROUP_CALL = "group.meeting"


class Signalling(WebsocketConsumer):
    def connect(self):

        self.user = self.scope["user"]
        isAuth = wsIsAuthenticated(self)
        if (not isAuth):
            self.close()
            return

        self.clean_user()
        self.add_user()
        self.accept()

    def disconnect(self, code):
        print("Disconnecting")
        isAuth = wsIsAuthenticated(self)
        if (not isAuth):
            pass
        else:
            self.clean_user()

    async def authenticate(self, data):

        scope = self.scope
        token = data['token']

        try:
            UntypedToken(token)
        except Exception as e:
            raise InvalidToken("Invalid Token")

        decoded = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user = get_user(validated_token=decoded)
        self.user = user

        print("HEy there")
        self.clean_user()
        self.add_user()
        print("Authenticated")

    def receive(self, text_data='', bytes_data=None, **kwargs):

        data = json.loads(text_data)
        event_type = data["type"]
        print("Sending ")
        print("Event Type :"+str(event_type))

        if (event_type == "authenticate"):
            # await self.send(json.dumps(data))
            self.channel_layer.send(self.channel_name, data)
            return

        data['mobile'] = self.user.mobile
        receivers_mobile = data["receivers"]
        for receiver_mobile in receivers_mobile:
            receiver_channel_name = self.get_channel(receiver_mobile)

            if (receiver_channel_name):
                print(f"Sending To {receiver_mobile}")
                print(f"CHANNEL_NAME : {receiver_channel_name}")

                async_to_sync(self.channel_layer.send)(
                    receiver_channel_name, data)

                if (event_type == OFFER):
                    self.send(json.dumps(
                        {"status": "online", "type": "status"}))
                return
            else:
                if (event_type == OFFER):
                    self.send(json.dumps(
                        {"status": "offline", "type": "status"}))

    def rtc_offer(self, text_data):
        print("Offer Getting")
        mobiles = text_data['receivers']
        for mobile in mobiles:
            print(f"Calling - {mobile}")
        self.send(json.dumps(text_data))

    def group_meeting(self, text_data):
        mobiles = text_data['receivers']
        for mobile in mobiles:
            print(f"Calling - {mobile}")
        self.send(json.dumps(text_data))

    def rtc_answer(self, text_data):
        self.send(json.dumps(text_data))

    def rtc_candidate(self, text_data):
        self.send(json.dumps(text_data))

    def rtc_hangup(self, text_data):
        self.send(json.dumps(text_data))

    def rtc_reject(self, text_data):
        self.send(json.dumps(text_data))

    def rtc_remote(self, text_data):
        self.send(json.dumps(text_data))

    def get_channel(self, mobile):
        try:
            channels = SignallingWSClient.objects.filter(
                user__mobile=int(mobile))
            print(f"{channels.count()} Channels with mobile no {mobile}")

        except Exception as e:
            pass

        if (channels.exists()):
            channel_name = channels.first().channel_name
            return channel_name
        else:
            return None

    def add_user(self):
        print("Createad Channel "+str(self.channel_name))
        SignallingWSClient.objects.create(
            user=self.user, channel_name=self.channel_name)
        print("User Added with mobile -- ", str(self.user.mobile))

    def clean_user(self):
        SignallingWSClient.objects.filter(user=self.user).delete()
