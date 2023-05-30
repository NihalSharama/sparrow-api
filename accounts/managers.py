from django.contrib.auth.models import BaseUserManager


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, mobile, password, **extra_fields):
        if(not mobile):
            raise ValueError("Invalid Mobile Number...")

        # Extra Fields
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(mobile=mobile, password=password, **extra_fields)
        user.save(using=self._db)

        return user

    def create_superuser(self, mobile, password, **extra_fields):

        if(not mobile):
            raise ValueError("Invalid Mobile Number...")

        # Extra Fields
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        user = self.model(mobile=mobile, password=password, **extra_fields)
        user.save(using=self._db)

        return user
