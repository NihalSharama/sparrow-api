from .views import ConversationAPI, ChatAPI, CallsAPI
from rest_framework.routers import SimpleRouter


router = SimpleRouter()
router.register("chats", ChatAPI, basename="chat_api")
router.register("conv", ConversationAPI, basename="conv_api")
router.register("calls", CallsAPI, basename="calls_api")

urlpatterns = router.urls
