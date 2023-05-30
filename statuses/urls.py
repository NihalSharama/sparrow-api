from .views import StatusAPI
from rest_framework.routers import SimpleRouter


router = SimpleRouter()
router.register("statuses", StatusAPI, basename="status_api")

urlpatterns = router.urls
