from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.models import User
from .models import Presupuesto, PermisoPresupuesto, Especialidad
from .serializers import PresupuestoSerializer, PermisoPresupuestoSerializer, EspecialidadSerializer
from .permissions import PuedeEditarPresupuesto
from coldrooms.models import ColdRoom
from equipos.models import (
    Evaporador, Compresor, Deshumificador, EnfriadorGlicol, 
    Condensador, Ventilador, BombaGlicol, Motor, Resistencia
)
from django.contrib.contenttypes.models import ContentType
import copy

class PresupuestoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestión de presupuestos.
    
    Permite crear, listar, actualizar y eliminar presupuestos.
    Los usuarios solo pueden ver los presupuestos que han creado,
    donde son responsables, o que han sido compartidos con ellos.
    
    ## Permisos por rol:
    
    | Rol | Crear | Ver todos | Ver propios | Editar | Eliminar | Compartir |
    |-----|-------|-----------|-------------|--------|----------|-----------|
    | Superadmin | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
    | Creador | ✓ | ✗ | ✓ | ✓ | ✓ | ✓ |
    | Ingeniero Responsable | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ |
    | Usuario con permiso | ✗ | ✗ | ✓ | Depende* | ✗ | ✗ |
    
    *Los usuarios con permiso 'escritura' pueden editar.
    """

    queryset = Presupuesto.objects.filter(activo=True)
    serializer_class = PresupuestoSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        """
        Permitir obtener objetos eliminados si es para restaurarlos
        """
        if self.action in ['update', 'partial_update'] and self.request.data.get('activo') is True:
            # Bypass del queryset filtrado
            from django.shortcuts import get_object_or_404
            obj = get_object_or_404(Presupuesto.objects.all(), pk=self.kwargs['pk'])
            self.check_object_permissions(self.request, obj)
            return obj
            
        return super().get_object()

    def get_permissions(self):
        """
        Asignar permisos especificos por accion        
        """
        if self.action in ['update', 'partial_update']:
            return [IsAuthenticated(), PuedeEditarPresupuesto()]
        
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        # Asignar creador automáticamente
        serializer.save(creado_por=self.request.user)
    
    def get_queryset(self):
        queryset = Presupuesto.objects.all()
        
        # Filtrar por estado activo/inactivo (Papelera)
        if self.request.query_params.get('activo') == 'False':
             queryset = queryset.filter(activo=False)
        else:
             queryset = queryset.filter(activo=True)
        user = self.request.user

        # Si es superusuario, ve todos
        if user.is_superuser:
            return queryset
        
        #1. Presupuestos creados por el usuario
        mis_presupuestos = queryset.filter(creado_por=user)

        #2. Presupuestos donde es ingeniero responsable
        como_responsable = queryset.filter(ingeniero_responsable=user)

        #3. Presupuestos compartidos con el usuario
        presupuestos_compartidos_ids = PermisoPresupuesto.objects.filter(
            usuario=user
        ).values_list('presupuesto_id', flat=True)
        compartidos = queryset.filter(id__in=presupuestos_compartidos_ids)

        # Unir todos
        return (mis_presupuestos | como_responsable | compartidos).distinct()
    

    def check_object_permissions(self, request, obj):
        """
            WORKAROUND para bug en DRF 3.16.1
            TODO: Revisar al actualizar DRF si esto sigue siendo necesario
            Issue: NameError al capturar PermisoPresupuesto.DoesNotExist
            Solución temporal: Sobrescribir método completo
        """
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                self.permission_denied(
                    request,
                    message=getattr(permission, 'message', None),
                    code=getattr(permission, 'code', None)
                )
    
    
    @action(detail=False, methods=['post'])
    def crear_presupuesto(self, request):
        """Endpoint específico para crear presupuesto desde el formulario"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {
                    'id': serializer.instance.id, 
                    'consecutivo': serializer.instance.consecutivo,
                    'message': 'Presupuesto creado exitosamente'
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def permisos(self, request, pk=None):
        """Listar todos los permisos de un presupuesto"""
        presupuesto = self.get_object()
        
        # Verificar que el usuario tiene permiso para ver los permisos
        if presupuesto.creado_por != request.user:
            return Response(
                {"error": "No tienes permiso para ver los permisos de este presupuesto."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        permisos = PermisoPresupuesto.objects.filter(presupuesto=presupuesto)
        serializer = PermisoPresupuestoSerializer(permisos, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def compartir(self, request, pk=None):
        """Compartir presupuesto con otro usuario"""
        presupuesto = self.get_object()
        
        # Verificar que el usuario es el creador
        if presupuesto.creado_por != request.user:
            return Response(
                {"error": "Solo el creador puede compartir el presupuesto."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        usuario_id = request.data.get('usuario_id')
        tipo_permiso = request.data.get('tipo_permiso', 'lectura')
        
        try:
            usuario = User.objects.get(id=usuario_id)
            
            # No compartir con uno mismo
            if usuario == request.user:
                return Response(
                    {"error": "No puedes compartir contigo mismo."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            permiso, created = PermisoPresupuesto.objects.get_or_create(
                presupuesto=presupuesto,
                usuario=usuario,
                defaults={'tipo_permiso': tipo_permiso}
            )
            
            if not created:
                permiso.tipo_permiso = tipo_permiso
                permiso.save()
            
            return Response({
                "message": f"Presupuesto compartido con {usuario.username}",
                "permiso": PermisoPresupuestoSerializer(permiso).data
            })
            
        except User.DoesNotExist:
            return Response(
                {"error": "Usuario no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'])
    def revocar_permiso(self, request, pk=None):
        """Revocar permiso a un usuario"""
        presupuesto = self.get_object()
        
        if presupuesto.creado_por != request.user:
            return Response(
                {"error": "Solo el creador puede revocar permisos."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        usuario_id = request.data.get('usuario_id')
        
        try:
            permiso = PermisoPresupuesto.objects.get(
                presupuesto=presupuesto,
                usuario_id=usuario_id
            )
            permiso.delete()
            
            return Response({
                "message": "Permiso revocado exitosamente."
            })
            
        except PermisoPresupuesto.DoesNotExist:
            return Response(
                {"error": "Permiso no encontrado."},
                status=status.HTTP_404_NOT_FOUND
            )
        
    def destroy(self, request, *args, **kwargs):
        """
        Sobrescribe el metodo de eliminacion fisica por una eliminacion logica
        """

        instance = self.get_object()

        #verificamos que solo el creador o un admin pueda borrar
        if not request.user.is_superuser and instance.creado_por != request.user:
            return Response(
                {"error": "No tienes permiso para eliminar este presupuesto."},
                status=status.HTTP_403_FORBIDDEN
            )
        #borrado logico
        instance.activo = False
        instance.save()

        return Response(
            {"message": "Presupuesto eliminado exitosamente."},
            status=status.HTTP_204_NO_CONTENT
        ) 
    
    @action(detail=True, methods=['post'])
    def restaurar(self, request, pk=None):
        """
        Accion para recuperar un presupuesto eliminado logicamente
        """
        try:
            presupuesto = Presupuesto.objects.get(pk=pk)
            presupuesto.activo = True
            presupuesto.save()
            return Response({"message":"Presupuesto restaurado correctamente."})
        except Presupuesto.DoesNotExist:
            return Response({"error":"Presupuesto no encontrado."}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def transferir_copia(self, request, pk=None):
        """
        Clona el presupuesto y lo asigna a otro usuario (Préstamo).
        """
        presupuesto = self.get_object()
        
        # Verificar permisos: solo el creador puede prestar
        if presupuesto.creado_por != request.user:
            return Response(
                {"error": "Solo el creador puede prestar el presupuesto."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        target_user_id = request.data.get('usuario_id')
        if not target_user_id:
            return Response({"error": "ID de usuario destino requerido."}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            target_user = User.objects.get(id=target_user_id)
        except User.DoesNotExist:
            return Response({"error": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
            
        # Clonar presupuesto
        nuevo_presupuesto = self._clonar_presupuesto(presupuesto, nuevo_creador=target_user)
        
        # Actualizar campos de préstamo
        nuevo_presupuesto.es_prestamo = True
        nuevo_presupuesto.dueno_original = request.user
        nuevo_presupuesto.presupuesto_padre = presupuesto # Opcional: mantener rastro
        nuevo_presupuesto.save()
        
        return Response({
            "message": f"Presupuesto prestado a {target_user.username}",
            "id": nuevo_presupuesto.id
        })

    @action(detail=True, methods=['post'])
    def devolver_version(self, request, pk=None):
        """
        Devuelve una versión modificada al dueño original.
        """
        presupuesto = self.get_object()
        
        # Verificar que es un préstamo
        if not presupuesto.es_prestamo or not presupuesto.dueno_original:
            return Response(
                {"error": "Este presupuesto no es un préstamo."},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Verificar que el usuario actual es quien tiene el préstamo
        if presupuesto.creado_por != request.user:
            return Response(
                {"error": "No tienes permiso para devolver este presupuesto."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        dueno_original = presupuesto.dueno_original
        
        # Clonar de vuelta al dueño original
        nuevo_presupuesto = self._clonar_presupuesto(presupuesto, nuevo_creador=dueno_original)
        
        # Configurar como versión devuelta (ya no es préstamo)
        nuevo_presupuesto.es_prestamo = False
        nuevo_presupuesto.dueno_original = None
        nuevo_presupuesto.presupuesto_padre = presupuesto
        
        # Actualizar nombre
        nuevo_presupuesto.nombre_proyecto = f"{presupuesto.nombre_proyecto} - Rev. {request.user.username}"
        nuevo_presupuesto.save()
        
        return Response({
            "message": "Versión devuelta al dueño original.",
            "id": nuevo_presupuesto.id
        })

    def _clonar_presupuesto(self, presupuesto_original, nuevo_creador):
        """
        Método auxiliar para realizar copia profunda de un presupuesto y sus items.
        """
        # 1. Copiar Presupuesto base
        nuevo = Presupuesto.objects.get(pk=presupuesto_original.pk)
        nuevo.pk = None
        nuevo.consecutivo = "" # Se generará uno nuevo al guardar
        nuevo.creado_por = nuevo_creador
        nuevo.ingeniero_responsable = nuevo_creador # O mantener el original? Asumimos el nuevo
        nuevo.save()
        
        # 2. Copiar M2M Especialidades
        nuevo.especialidades.set(presupuesto_original.especialidades.all())
        
        # 3. Copiar ColdRooms y sus Equipos
        for cr in presupuesto_original.cold_rooms.all():
            old_cr_pk = cr.pk
            cr.pk = None
            cr.presupuesto = nuevo
            cr.save()
            
            # Recuperar instancia original para buscar hijos
            cr_original = ColdRoom.objects.get(pk=old_cr_pk)
            
            # Copiar Equipos por tipo
            equipo_models = [
                Evaporador, Compresor, Deshumificador, EnfriadorGlicol, 
                Condensador, Ventilador, BombaGlicol
            ]
            
            for ModelClass in equipo_models:
                # Buscar equipos relacionados a este ColdRoom
                # Usamos el related_name inverso predeterminado o inferido
                # ColdRoom tiene related_name="%(app_label)s_%(class)s_related" en el modelo abstracto Equipo
                related_name = f"{ModelClass._meta.app_label}_{ModelClass._meta.model_name}_related"
                
                if hasattr(cr_original, related_name):
                    manager = getattr(cr_original, related_name)
                    for equipo in manager.all():
                        self._clonar_equipo(equipo, cr)

        return nuevo

    def _clonar_equipo(self, equipo_original, nuevo_cold_room):
        """Helper para clonar equipo y sus componentes"""
        old_pk = equipo_original.pk
        
        # Clonar equipo
        equipo_original.pk = None
        equipo_original.cold_room = nuevo_cold_room
        equipo_original.save()
        new_equipo = equipo_original
        
        # Recuperar original para componentes
        # Necesitamos la clase concreta para consultar generic relations si no estan precargadas
        # Pero GenericRelation 'motores' y 'resistencias' estan en el modelo
        
        # Sin embargo, al hacer .pk = None, perdimos el acceso a los reversos del objeto original en memoria si no tuvimos cuidado
        # Mejor re-consultar el original usando old_pk y la clase del objeto
        original_db = type(equipo_original).objects.get(pk=old_pk)
        
        # Copiar Motores
        if hasattr(original_db, 'motores'):
            for motor in original_db.motores.all():
                motor.pk = None
                motor.content_object = new_equipo
                motor.save()
                
        # Copiar Resistencias
        if hasattr(original_db, 'resistencias'):
            for res in original_db.resistencias.all():
                res.pk = None
                res.content_object = new_equipo
                res.save()
class PermisoPresupuestoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar permisos de presupuestos.
    """
    queryset = PermisoPresupuesto.objects.all()
    serializer_class = PermisoPresupuestoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Solo ver permisos de presupuestos que el usuario creó
        return PermisoPresupuesto.objects.filter(
            presupuesto__creado_por=self.request.user
        )
    
    def perform_create(self, serializer):
        presupuesto = serializer.validated_data['presupuesto']
        
        # Verificar que el usuario sea el creador del presupuesto
        if presupuesto.creado_por != self.request.user:
            raise serializers.ValidationError(
                "Solo el creador del presupuesto puede compartirlo."
            )
        
        serializer.save()


class EspecialidadViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para listar especialidades disponibles.
    """
    queryset = Especialidad.objects.all()
    serializer_class = EspecialidadSerializer

