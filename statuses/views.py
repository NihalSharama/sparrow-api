from itertools import chain
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from .serializers import StatusSerializer
from sparrow.utils import resp_fail, resp_success
from .models import Status
from chats.models import Conversation
from .serializers import UserSerializer
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q


class StatusAPI(ModelViewSet):
    serializer_class = StatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Status.objects.filter(user=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        current_user = UserSerializer(request.user).data

        conversations = list(chain(Conversation.objects.filter(
            user1=current_user['id']), Conversation.objects.filter(user2=current_user['id'])))

        time_threshold = timezone.now() - timezone.timedelta(hours=24)

        all_status = Status.objects.filter(
            ~Q(created_at__lt=time_threshold)).all()
        my_status = Status.objects.filter(
            ~Q(created_at__lt=time_threshold) & ~Q(user=self.request.user))

        contact_status = []
        for conversation in conversations:
            for status in all_status:
                if (status.user == conversation.user1 or status.user == conversation.user2) & (self.request.user != status.user):
                    status = StatusSerializer(
                        status, context={'status_info': status}).data
                    contact_status.append(status)

        import itertools
        contact_status = itertools.groupby(
            contact_status, lambda x: x['user_mobile'])

        grpd_contact_status = []
        for mobile, status in contact_status:
            grpd_contact_status.append({mobile: list(status)})

        my_status = StatusSerializer(my_status, many=True, context={
                                     'status_info': my_status.first()}).data

        return Response(
            resp_success("Status Featched Successfully", {
                         "data": {'my_status': my_status, 'contact_status': grpd_contact_status}})
        )

    def create(self, request, *args, **kwargs):
        request.data["user"] = request.user.id
        status_form = StatusSerializer(
            data=request.data)
        if (status_form.is_valid()):
            status = status_form.save()
            return Response(
                resp_success("Status Uploaded Successfully",
                             {"data": status_form.data}))
        else:
            return Response(
                resp_fail("Failed To Upload Status",
                          {"errors": status_form.errors}))

    @action(methods=["POST"], detail=False, url_path="view_status")
    def view_status(self,  request):
        try:

            status = Status.objects.filter(
                id=int(request.data['status_id']))[0]

            status.views.add(request.user.id)

            status.save()
            status = StatusSerializer(
                status, many=False)

            return Response(
                resp_success("Viewed",
                             status.data))
        except Exception:
            return resp_fail("Failed To Upload Status",
                             {"errors": ''})
