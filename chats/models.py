from django.db import models
from accounts.models import User
from django.db.models.manager import Manager


# Create your models here.


class Conversation(models.Model):
    user1 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="convs1")
    user2 = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="convs2")
    archivedBy = models.ManyToManyField(
        User, related_name='archived_chats', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class GroupChat(models.Model):
    group_name = models.CharField(max_length=255)
    group_profile = models.ImageField(upload_to="profilepics",
                                      default="profilepics/default-group.jpg")
    users = models.ManyToManyField(User, related_name='group')
    admins = models.ManyToManyField(User, related_name='admin_of')
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='creator_of')
    archivedBy = models.ManyToManyField(
        User, related_name='archived_groups', blank=True)
    # isArchived = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages", null=True)
    group = models.ForeignKey(
        GroupChat, on_delete=models.CASCADE, related_name="messages", null=True)
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages")

    receivers = models.ManyToManyField(User, related_name='received_messages')
    message = models.TextField()
    isStarred = models.BooleanField(default=False)
    replyOf = models.TextField(null=True)

    STATUS_CHOICES = [
        (0, "SENT"),
        (1, "DELIVERED"),
        (2, "SEEN"),
    ]

    status = models.IntegerField(choices=STATUS_CHOICES, default=0)
    created_at = models.DateTimeField(auto_now_add=True)


class CallLog(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="calls", null=True)
    group = models.ForeignKey(
        GroupChat, on_delete=models.CASCADE, related_name="calls", null=True)
    participants = models.ManyToManyField(
        User, related_name='logs', blank=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='created_calls')
    created_at = models.DateTimeField(auto_now_add=True)


class Document(models.Model):
    message = models.ForeignKey(
        Message, on_delete=models.CASCADE, related_name="documents")
    document = models.FileField(upload_to="documents/")
    created_at = models.DateTimeField(auto_now_add=True)


class Image(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    document = models.ImageField(upload_to="images/")
    created_at = models.DateTimeField(auto_now_add=True)


# WebSockets --Models
class WSClient(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel_name = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class GroupWSClient(models.Model):
    group = models.ForeignKey(GroupChat, on_delete=models.CASCADE)
    users = models.ManyToManyField(User, related_name='ws_group')

    channel_name = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class SignallingWSClient(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel_name = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


# For Deleting Conversation
class DeletedConversation(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="deleted_convs")
    conv = models.OneToOneField(
        Conversation, on_delete=models.CASCADE, related_name="deleted")
    deleted_at = models.DateTimeField(auto_now_add=True)
