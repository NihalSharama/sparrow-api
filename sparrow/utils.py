from multiprocessing import reduction
import phonenumbers
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from accounts.models import User
from rest_framework.serializers import ModelSerializer
import re


def required_data(data_dict, data_list):
    errors = {}

    data = []

    for d in data_list:
        value = data_dict.get(d, None)
        if (not value):
            errors[d] = "This Field Is Required"

        data.append(value)

    if (len(list(errors.values())) == 0):
        return True, data

    return False, errors


def resp_success(message, data={}, status_code=200):

    return {
        'success': True,
        "message": message,
        "data": data,
        "status_code": status_code
    }


def resp_fail(error_msg, data={}, error_code=401):

    return {
        'success': False,
        "message": error_msg,
        "data": data,
        "status_code": error_code
    }


def user_created(user):
    user.is_created = True
    user.save()


def get_model(model, **args):
    obj_list = model.objects.filter(**args)

    if (obj_list.exists()):
        return {"exist": True, "data": obj_list.first()}

    return {"exist": False, "data": []}


def user_exists(mobile):
    return User.objects.filter(mobile=mobile).exists()


def phone_format(phone_number):

    clean_phone_number = re.sub('[^0-9]+', '', phone_number)
    formatted_phone_number = re.sub(r'\D', '', clean_phone_number)
    if (formatted_phone_number.startswith("+91")):
        formatted_phone_number = formatted_phone_number[3:]
    return formatted_phone_number
