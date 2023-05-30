# Conversation
def get_conv_messages(conv, user):
    if (hasattr(conv, "deleted")):

        if user == conv.deleted.user:
            deleted_at = conv.deleted.deleted_at
            return conv.messages.filter(created_at__gt=deleted_at)
        return conv.messages.all().order_by('-created_at')
    else:
        return conv.messages.all().order_by('-created_at')


def get_group_messages(group, user):
    if (hasattr(group, "deleted")):

        if user == group.deleted.user:
            deleted_at = group.deleted.deleted_at
            return group.messages.filter(created_at__gt=deleted_at)
        return group.messages.all().order_by('-created_at')
    else:
        return group.messages.all().order_by('-created_at')
