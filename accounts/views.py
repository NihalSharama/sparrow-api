from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from accounts.models import User, LoginOtp
import random
from sparrow.utils import required_data, resp_fail, resp_success, get_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OtpTempData
from .services import send_otp, verify_otp
from .serializers import UserSerializer
import os
# Create your views here.


class AuthAPI(ViewSet):

    @action(methods=["POST"], detail=False, url_path="send_otp")
    def send_otp(self, request, *args, **kwargs):
        data = request.data
        success, req_data = required_data(data, ["mobile"])
        if (not success):
            return Response(resp_fail("Mobile No. Required "))

        mobile, = req_data
        try:
            # Verification Goes Here
            mobile = int(mobile)
        except Exception as e:
            return Response(resp_fail("Mobile No Not Valid.."))

        users_list = User.objects.filter(mobile=mobile)
        user_exist = users_list.exists()

        return send_otp(user_exist, mobile, data,
                        'auth')

    @action(methods=["POST"], detail=False, url_path="verify_otp")
    def verify_otp(self, request, *args, **kwargs):
        data = request.data
        success, req_data = required_data(data, ["mobile", "otp"])

        if (not success):
            return Response(resp_fail("[mobile,otp] Is Required ..."))

        mobile, otp = req_data
        users_list = User.objects.filter(mobile=mobile)

        return verify_otp(users_list, mobile, otp, 'auth')


class ProfileAPI(ViewSet):

    @action(methods=["POST"], detail=False, url_path="update-profile")
    def update_profile(self, request, *args, **kwargs):
        data = self.request.data

        if len(data) == 0:
            return resp_fail("No Data Found")

        user = UserSerializer(self.request.user, data=data,  partial=True)

        if user.is_valid():
            user.save()
            return Response(
                resp_success("Profile Updated Succesfully", {"data": user.data}))

        return Response(
            resp_fail("Failed To Update Profile"))

    @action(methods=["POST"], detail=False, url_path="update-profile-pic")
    def update_profile_pic(self, request, *args, **kwargs):
        file_data = self.request.data

        user = UserSerializer(
            self.request.user, data=file_data, partial=True)

        # remove old profile pic
        if (user.is_valid()):
            try:
                old_user = UserSerializer(self.request.user
                                          ).data

                if old_user['profile_pic'].split('/')[3] != 'default.jpg':
                    file_path = old_user['profile_pic']
                    os.remove(file_path[1:])
            except Exception:
                resp_fail("Failed To Change Profile",
                          {"errors": user.errors})
            user.save()
            return Response(
                resp_success("Profile Uploaded Successfully",
                             {"data": user.data}))
        else:
            return Response(
                resp_fail("Failed To Change Profile",
                          {"errors": user.errors}))

    @action(methods=["DELETE"], detail=False, url_path="remove-profile-pic")
    def remove_profile_pic(self, request, *args, **kwargs):

        user = self.request.user

        for f in user._meta.fields:
            if f.name == 'profile_pic':
                setattr(user, f.name, f.default)

        # remove old profile pic
        try:
            old_user = UserSerializer(self.request.user
                                      ).data

            if old_user['profile_pic'].split('/')[3] != 'default.jpg':
                file_path = old_user['profile_pic']
                os.remove(file_path[1:])
        except Exception:
            resp_fail("Failed To Remove Profile",
                      {"errors": user})

        user.save()
        data = UserSerializer(user).data

        return Response(
            resp_success("Profile Removed Successfully",
                         {"data": data}))

    @action(methods=["POST"], detail=False, url_path="send_otp")
    def send_otp(self, request, *args, **kwargs):
        data = request.data
        success, req_data = required_data(
            data, ["mobile", "action"])
        if (not success):
            return Response(resp_fail("Mobile & action Required "))

        mobile,  action = req_data
        try:
            # Verification Goes Here
            mobile = int(mobile)
        except Exception as e:
            return Response(resp_fail("Mobile No. Not Valid.."))

        users_list = User.objects.filter(mobile=mobile)
        user_exist = users_list.exists()

        if action == 'change-number':
            return send_otp(user_exist, int(data['new_mobile']), data, action)
        elif action == 'delete-user':
            return send_otp(user_exist, mobile, data, action)

    @action(methods=["POST"], detail=False, url_path="verify_otp")
    def verify_otp(self, request, *args, **kwargs):
        data = request.data

        success, req_data = required_data(
            data, ["mobile", "otp", "action"])

        if (not success):
            return Response(resp_fail("[mobile,otp, action] Is Required ..."))

        mobile, otp, action = req_data
        try:
            # Verification Goes Here
            mobile = int(mobile)
        except Exception as e:
            return Response(resp_fail("Mobile No. Not Valid.."))

        users_list = User.objects.filter(mobile=mobile)

        if action == 'change-number':
            return verify_otp(users_list, int(data['new_mobile']), otp,  action)
        elif action == 'delete-user':
            return verify_otp(users_list, mobile, otp,  action)
