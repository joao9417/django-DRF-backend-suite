from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import ColdRoom
from .serializers import ColdRoomSerializer
from presupuestos.models import Presupuesto

class ColdRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ColdRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtra los cuartos fríos según los permisos del usuario"""
        user = self.request.user
        queryset = ColdRoom.objects.all()
        
        # Si no es superusuario, filtrar por permisos
        if not user.is_superuser:
            queryset = queryset.filter(
                presupuesto__creado_por=user
            ) | queryset.filter(
                presupuesto__ingeniero_responsable=user
            )
        
        # Filtrar por presupuesto si se proporciona el parámetro
        presupuesto_id = self.request.query_params.get('presupuesto_id')
        if presupuesto_id:
            queryset = queryset.filter(presupuesto_id=presupuesto_id)
        
        return queryset.distinct().order_by('-creado_en')
    
    def get_serializer_context(self):
        """Incluye el request en el contexto del serializer"""
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        """Guarda el cuarto frío con validaciones adicionales"""
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def por_presupuesto(self, request):
        """Obtiene todos los cuartos fríos de un presupuesto específico"""
        presupuesto_id = request.query_params.get('presupuesto_id')
        
        if not presupuesto_id:
            return Response(
                {'error': 'Se requiere el parámetro presupuesto_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar que el usuario tenga acceso al presupuesto
        user = request.user
        try:
            presupuesto = Presupuesto.objects.get(id=presupuesto_id)
            if not user.is_superuser:
                if presupuesto.creado_por != user and presupuesto.ingeniero_responsable != user:
                    return Response(
                        {'error': 'No tienes acceso a este presupuesto'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        except Presupuesto.DoesNotExist:
            return Response(
                {'error': 'Presupuesto no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener cuartos fríos del presupuesto
        cold_rooms = ColdRoom.objects.filter(presupuesto_id=presupuesto_id)
        serializer = self.get_serializer(cold_rooms, many=True)
        
        # Incluir información del presupuesto en la respuesta
        return Response({
            'presupuesto': {
                'id': presupuesto.id,
                'nombre_proyecto': presupuesto.nombre_proyecto,
                'consecutivo': presupuesto.consecutivo,
            },
            'cold_rooms': serializer.data,
            'total': cold_rooms.count(),
            'volumen_total': sum(room.volumen for room in cold_rooms)
        })
    
    @action(detail=True, methods=['get'])
    def resumen(self, request, pk=None):
        """Devuelve un resumen detallado del cuarto frío"""
        cold_room = self.get_object()
        
        # Calcular área de paredes, techo, piso
        area_paredes = 2 * (cold_room.alto * cold_room.ancho + cold_room.alto * cold_room.largo)
        area_piso_techo = 2 * (cold_room.ancho * cold_room.largo)
        
        resumen = {
            'id': cold_room.id,
            'nombre_cuarto': cold_room.nombre_cuarto,
            'dimensiones': {
                'ancho': float(cold_room.ancho),
                'largo': float(cold_room.largo),
                'alto': float(cold_room.alto),
                'volumen': float(cold_room.volumen),
            },
            'temperatura': float(cold_room.temperatura_requerida),
            'areas': {
                'paredes_m2': float(area_paredes),
                'piso_techo_m2': float(area_piso_techo),
                'total_m2': float(area_paredes + area_piso_techo),
            },
            'relacion_superficie_volumen': float((area_paredes + area_piso_techo) / cold_room.volumen) if cold_room.volumen > 0 else 0,
            'presupuesto': {
                'id': cold_room.presupuesto.id,
                'nombre': cold_room.presupuesto.nombre_proyecto,
            }
        }
        
        return Response(resumen)