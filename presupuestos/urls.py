from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PresupuestoViewSet, PermisoPresupuestoViewSet, EspecialidadViewSet

router = DefaultRouter()
router.register(r'presupuestos', PresupuestoViewSet, basename='presupuesto')
router.register(r'permisos', PermisoPresupuestoViewSet, basename='permiso')
router.register(r'especialidades', EspecialidadViewSet, basename='especialidad')

urlpatterns = [
    path('', include(router.urls)),
]