from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import EquipoViewSet, MotorViewSet, ResistenciaViewSet

router = DefaultRouter()
router.register(r'equipos', EquipoViewSet, basename='equipo')
router.register(r'motores', MotorViewSet, basename='motor')
router.register(r'resistencias', ResistenciaViewSet, basename='resistencia')

urlpatterns = [
    path('', include(router.urls)),
]