from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PresupuestoViewSet, PermisoPresupuestoViewSet

router = DefaultRouter()
router.register(r'presupuestos', PresupuestoViewSet, basename='presupuesto')
router.register(r'permisos', PermisoPresupuestoViewSet, basename='permiso')

urlpatterns = [
    path('', include(router.urls)),
]