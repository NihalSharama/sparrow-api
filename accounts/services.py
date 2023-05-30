from .models import *
import random
from rest_framework.response import Response
from sparrow.utils import resp_fail, resp_success, required_data
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer
import os


import requests


def delete_otps(user_exist, mobile):
    if (user_exist):
        LoginOtp.objects.filter(mobile=mobile).delete()
    else:
        OtpTempData.objects.filter(mobile=mobile).delete()


def send_otp_sms(mobile, msg):

    requests.get(
        url=f'http://sms.domainadda.com/vendorsms/pushsms.aspx?user=kotasaketh&password=123456&msisdn={mobile}&sid=152535&msg={msg}&fl=0&gwid=2')


def send_otp(user_exist, mobile, data, request_type):
    delete_otps(user_exist, mobile)
    if request_type == 'auth':
        if (user_exist):
            # Login
            otp = random.randint(10000, 99999)
            otp_obj = LoginOtp(otp=otp, mobile=mobile)
            otp_obj.save()
            return Response(
                resp_success("OTP Sent Successfully!", {
                    "otp": otp,
                    "mobile": mobile
                }))
        else:
            # SignUP
            success, req_data = required_data(
                data, ["first_name", "last_name"])
            if (not success):
                return Response(resp_fail("[first_name,last_name] Required..."))

            first_name, last_name = req_data
            otp = random.randint(10000, 99999)

            otp_obj = OtpTempData(first_name=first_name,
                                  last_name=last_name,
                                  otp=otp,
                                  mobile=mobile)
            otp_obj.save()

            return Response(
                resp_success("OTP Sent Successfully!", {
                    "otp": otp,
                    "mobile": mobile
                }))

    elif request_type == 'change-number':
        otp = random.randint(10000, 99999)
        otp_obj = ChangeNumberOtp(otp=otp, mobile=mobile)
        otp_obj.save()
        return Response(
            resp_success("OTP Sent Successfully!", {
                "otp": otp,
                "mobile": mobile
            }))

    elif request_type == 'delete-user':
        otp = random.randint(10000, 99999)
        otp_obj = DeleteUserOtp(otp=otp, mobile=mobile)
        otp_obj.save()
        return Response(
            resp_success("OTP Sent Successfully!", {
                "otp": otp,
                "mobile": mobile
            }))


def verify_otp(users_list, mobile, otp, verify_type):
    action = ""
    user_exist = users_list.exists()
    if verify_type == 'auth':
        if (user_exist):
            user_otp = LoginOtp.objects.filter(mobile=mobile)
            user = users_list.first()
            action = "Login"
        else:
            action = "SignUp"
            user_otp = OtpTempData.objects.filter(mobile=mobile)

    elif verify_type == 'change-number':
        user_otp = ChangeNumberOtp.objects.filter(mobile=mobile)
        user = users_list.first()
        action = "Change Number"

    elif verify_type == 'delete-user':
        user_otp = DeleteUserOtp.objects.filter(mobile=mobile)
        user = users_list.first()
        action = "Delete User"

    if (user_otp.exists()):
        user_otp = user_otp.first()
        print(user_otp.otp)
        print(int(otp))
        if (user_otp.otp == int(otp)):
            if verify_type == 'auth':
                if (not user_exist):
                    user = User.objects.create(first_name=user_otp.first_name,
                                               last_name=user_otp.last_name,
                                               mobile=mobile)

                delete_otps(user_exist, mobile)
                token = RefreshToken.for_user(user)
                user_data = UserSerializer(user, many=False, ).data

                return Response(
                    resp_success(
                        f"{action} Successfully!", {
                            "refresh": str(token),
                            "token": str(token.access_token),
                            "user": user_data
                        }))

            elif verify_type == 'change-number':

                ChangeNumberOtp.objects.filter(mobile=mobile).delete()
                user_form = UserSerializer(
                    user, data={"mobile": mobile}, partial=True)

                if (user_form.is_valid()):
                    user_form.save()

                    new_user = User.objects.filter(mobile=mobile)
                    token = RefreshToken.for_user(new_user.first())
                    return Response(
                        resp_success(
                            f"{action} Successfully!", {
                                "refresh": str(token),
                                "token": str(token.access_token),
                                "user": user_form.data
                            }))
                else:
                    return Response(resp_fail("Failed To Change Number", {"errors": user_form.errors}))

            elif verify_type == 'delete-user':

                DeleteUserOtp.objects.filter(mobile=mobile).delete()
                user.delete()

                return Response(
                    resp_success(
                        f"{action} Successfully!"))

        else:
            attempts = 5 - user_otp.attempts
            user_otp.attempts += 1
            user_otp.save()
            if (attempts <= 0):
                if verify_type == 'auth':
                    if (user_exist):
                        LoginOtp.objects.filter(mobile=mobile).delete()
                    else:
                        OtpTempData.objects.filter(mobile=mobile).delete()
                elif verify_type == 'change-number':
                    ChangeNumberOtp.objects.filter(mobile=mobile).delete()

                return Response(resp_fail("No OTP Found.."))
            return Response(resp_fail(f"Wrong OTP Attempts - {attempts} LEFT"))
    else:
        return Response(resp_fail("No OTP Found.."))
