from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from accounts.managers import CustomUserManager
from simple_history.models import HistoricalRecords
# Create your models here.


class User(AbstractUser):
    username = None
    email = models.EmailField(blank=True)
    mobile = models.BigIntegerField(blank=False, unique=True)
    profile_pic = models.ImageField(upload_to="profilepics",
                                    default="profilepics/default.jpg")
    USERNAME_FIELD = 'mobile'

    REQUIRED_FIELDS = ["first_name", "last_name"]

    bio = models.TextField()
    objects = CustomUserManager()

    class GenderChoices(models.TextChoices):
        MALE = "male", "Male"
        FEMALE = "female", "Female"
        OTHER = "other", "Other"

    gender = models.CharField(max_length=255,
                              choices=GenderChoices.choices,
                              default=GenderChoices.MALE)

    history = HistoricalRecords()

    def __str__(self) -> str:
        return f"m-{self.first_name + ' '+ self.last_name}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.set_password(self.password)

        return super().save(*args, **kwargs)


# OTP Temp Data
class OtpTempData(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    mobile = models.IntegerField()
    attempts = models.IntegerField(default=0)
    otp = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()


# OTP Models
class LoginOtp(models.Model):
    otp = models.IntegerField()
    mobile = models.BigIntegerField()
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()


class ChangeNumberOtp(models.Model):
    otp = models.IntegerField()
    mobile = models.BigIntegerField()
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()


class DeleteUserOtp(models.Model):
    otp = models.IntegerField()
    mobile = models.BigIntegerField()
    attempts = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    history = HistoricalRecords()
