from channels.middleware import BaseMiddleware
from django.db import close_old_connections
from django.contrib.auth.models import AnonymousUser
from jwt import decode as jwt_decode
from channels.db import database_sync_to_async
from rest_framework_simplejwt.exceptions import InvalidToken
from rest_framework_simplejwt.tokens import UntypedToken
from django.conf import settings
from accounts.models import User


@database_sync_to_async
def get_user(validated_token):

    try:
        user = User.objects.get(id=validated_token["user_id"])
        return user

    except User.DoesNotExist:
        return AnonymousUser()


def get_user_sync(validated_token):

    try:
        user = User.objects.get(id=validated_token["user_id"])
        return user

    except User.DoesNotExist:
        raise AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):

    async def __call__(self, scope, receive, send):
        close_old_connections()
        # Query Params
        headers = {key.decode("ascii"): value.decode("ascii")
                   for key, value in scope['headers']}
        token = headers.get("token", "adioda")

        try:
            UntypedToken(token)
        except Exception as e:
            raise InvalidToken("Invalid Token")

        decoded = jwt_decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        scope["user"] = await get_user(validated_token=decoded)

        return await super().__call__(scope, receive, send)
