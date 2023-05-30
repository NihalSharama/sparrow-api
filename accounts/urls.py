from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from rest_framework.routers import SimpleRouter
from .views import AuthAPI, ProfileAPI

router = SimpleRouter()
router.register("auth", AuthAPI, basename="auth")
router.register("profile", ProfileAPI, basename="profile")

urlpatterns = router.urls
