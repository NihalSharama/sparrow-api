from django.db import models
from accounts.models import User


class Status(models.Model):
    media = models.FileField(upload_to="status/")
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="status_all")
    views = models.ManyToManyField(User, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

# Create your models here.
