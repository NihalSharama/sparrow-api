from django.contrib.auth.models import AnonymousUser


def wsIsAuthenticated(self):
    if (self.scope["user"] == AnonymousUser()):
        return False
    return True
