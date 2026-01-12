# permissions.py - VERSIÓN SIMPLIFICADA
from rest_framework.permissions import BasePermission 

class PuedeEditarPresupuesto(BasePermission):
    """
    Permiso personalizado para editar presupuestos.
    """
    message = "No tienes permiso para realizar esta acción."

    def has_object_permission(self, request, view, obj):
        # 1. El creador siempre puede editar
        if obj.creado_por == request.user:
            return True
        
        # 2. El ingeniero responsable NO puede editar
        if obj.ingeniero_responsable == request.user:
            self.message = "El ingeniero responsable no puede editar el presupuesto."
            return False
        
        # 3. Verificar permisos compartidos sin try/except complicado
        # Evitar importación circular importando aquí
        from .models import PermisoPresupuesto
        
        # Buscar permiso directamente
        permisos = PermisoPresupuesto.objects.filter(
            presupuesto=obj,
            usuario=request.user,
            tipo_permiso='escritura'
        )
        
        if permisos.exists():
            return True
        
        # Si llegamos aquí, no tiene permiso
        permisos_lectura = PermisoPresupuesto.objects.filter(
            presupuesto=obj,
            usuario=request.user,
            tipo_permiso='lectura'
        )
        
        if permisos_lectura.exists():
            self.message = "Solo tienes permiso de lectura sobre este presupuesto."
        else:
            self.message = "No tienes permiso para editar este presupuesto."
        
        return False