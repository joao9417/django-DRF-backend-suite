from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ColdRoomViewSet

router = DefaultRouter()
router.register(r'coldrooms', ColdRoomViewSet, basename='coldroom')

urlpatterns = [
    path('', include(router.urls)),
]