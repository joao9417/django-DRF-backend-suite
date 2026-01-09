from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q

from .models import (
    Evaporador, Compresor, Condensador, Deshumificador, 
    EnfriadorGlicol, Ventilador, BombaGlicol,
    Motor, Resistencia
)
from .serializers import (
    EquipoPolymorphicSerializer, EquipoListSerializer,
    MotorSerializer, ResistenciaSerializer
)
from coldrooms.models import ColdRoom

class EquipoViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar todos los tipos de equipos de manera polimórfica.
    """
    serializer_class = EquipoPolymorphicSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # Configuración de filtros y búsqueda
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['tipo_equipo', 'cold_room']
    search_fields = ['nombre', 'marca', 'modelo']
    ordering_fields = ['nombre', 'creado_en', 'tipo_equipo']
    ordering = ['-creado_en']
    
    def get_queryset(self):
        """
        Obtiene el queryset combinado de todos los tipos de equipos
        según los permisos del usuario.
        """
        user = self.request.user
        
        # Parámetros de filtrado
        tipo_equipo = self.request.query_params.get('tipo_equipo')
        cold_room_id = self.request.query_params.get('cold_room_id')
        
        # Construir querysets para cada tipo de equipo
        querysets = []
        
        # Mapeo de tipos de equipo a sus modelos
        tipo_model_map = {
            'evaporador': Evaporador,
            'compresor': Compresor,
            'condensador': Condensador,
            'deshumificador': Deshumificador,
            'enfriador_glicol': EnfriadorGlicol,
            'ventilador': Ventilador,
            'bomba_glicol': BombaGlicol,
        }
        
        # Si se especifica un tipo, solo usar ese modelo
        if tipo_equipo and tipo_equipo in tipo_model_map:
            model_class = tipo_model_map[tipo_equipo]
            querysets = [model_class.objects.all()]
        else:
            # Si no se especifica tipo, usar todos los modelos
            querysets = [model_class.objects.all() for model_class in tipo_model_map.values()]
        
        # Aplicar filtros comunes
        filtered_querysets = []
        for queryset in querysets:
            # Filtrar por cold_room si se especifica
            if cold_room_id:
                queryset = queryset.filter(cold_room_id=cold_room_id)
            
            # Filtrar por permisos del usuario
            if not user.is_superuser:
                queryset = queryset.filter(
                    Q(cold_room__presupuesto__creado_por=user) |
                    Q(cold_room__presupuesto__ingeniero_responsable=user)
                )
            
            filtered_querysets.append(queryset.select_related(
                'cold_room', 'cold_room__presupuesto'
            ))
        
        # Combinar todos los querysets
        from itertools import chain
        return list(chain(*filtered_querysets))
    
    def get_object(self):
        """
        Obtiene un objeto específico basado en su tipo.
        """
        # Obtener el ID del objeto
        pk = self.kwargs.get('pk')
        
        # Intentar encontrar el objeto en cada tipo de equipo
        tipos_equipo = [
            Evaporador, Compresor, Condensador, Deshumificador,
            EnfriadorGlicol, Ventilador, BombaGlicol
        ]
        
        for model_class in tipos_equipo:
            try:
                obj = model_class.objects.get(pk=pk)
                # Verificar permisos
                self.check_object_permissions(self.request, obj)
                return obj
            except model_class.DoesNotExist:
                continue
        
        # Si no se encuentra en ningún modelo
        raise Http404(f"No se encontró equipo con ID {pk}")
    
    def perform_create(self, serializer):
        """Guarda el equipo con validación de permisos"""
        # La validación de permisos se hace en el serializer
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def listar_simplificado(self, request):
        """
        Endpoint para listar equipos con información básica (más rápido).
        """
        queryset = self.get_queryset()
        serializer = EquipoListSerializer(queryset, many=True)
        
        # Calcular estadísticas
        estadisticas = {
            'total_equipos': len(queryset),
            'por_tipo': {},
            'potencia_total_kw': 0,
            'consumo_total_a': 0,
        }
        
        for equipo in queryset:
            # Contar por tipo
            tipo = equipo.tipo_equipo
            estadisticas['por_tipo'][tipo] = estadisticas['por_tipo'].get(tipo, 0) + 1
            
            # Sumar potencias y consumos
            if hasattr(equipo, 'potencia_total'):
                estadisticas['potencia_total_kw'] += equipo.potencia_total.get('total', {}).get('kilowatts', 0)
            
            if hasattr(equipo, 'consumo_total'):
                estadisticas['consumo_total_a'] += equipo.consumo_total.get('total_amperios', 0)
        
        return Response({
            'estadisticas': estadisticas,
            'equipos': serializer.data,
        })
    
    @action(detail=False, methods=['get'])
    def por_cuarto(self, request):
        """
        Obtener todos los equipos de un cuarto frío específico.
        """
        cold_room_id = request.query_params.get('cold_room_id')
        
        if not cold_room_id:
            return Response(
                {'error': 'Se requiere el parámetro cold_room_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verificar permisos sobre el cuarto frío
        user = request.user
        try:
            cold_room = ColdRoom.objects.get(id=cold_room_id)
            if not user.is_superuser:
                presupuesto = cold_room.presupuesto
                if presupuesto.creado_por != user and presupuesto.ingeniero_responsable != user:
                    return Response(
                        {'error': 'No tienes acceso a este cuarto frío'},
                        status=status.HTTP_403_FORBIDDEN
                    )
        except ColdRoom.DoesNotExist:
            return Response(
                {'error': 'Cuarto frío no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Obtener equipos del cuarto
        equipos = self.get_queryset().filter(cold_room_id=cold_room_id)
        serializer = self.get_serializer(equipos, many=True)
        
        # Calcular totales por cuarto
        potencia_total_kw = 0
        consumo_total_a = 0
        
        for equipo in equipos:
            if hasattr(equipo, 'potencia_total'):
                potencia_total_kw += equipo.potencia_total.get('total', {}).get('kilowatts', 0)
            
            if hasattr(equipo, 'consumo_total'):
                consumo_total_a += equipo.consumo_total.get('total_amperios', 0)
        
        return Response({
            'cold_room': {
                'id': cold_room.id,
                'nombre': cold_room.nombre_cuarto,
                'temperatura': float(cold_room.temperatura_requerida),
                'volumen': float(cold_room.volumen),
            },
            'equipos': serializer.data,
            'resumen_electrico': {
                'cantidad_equipos': equipos.count(),
                'potencia_total_kw': potencia_total_kw,
                'consumo_total_a': consumo_total_a,
            }
        })
    
    @action(detail=True, methods=['get'])
    def componentes(self, request, pk=None):
        """
        Obtener todos los componentes eléctricos de un equipo.
        """
        equipo = self.get_object()
        
        motores = Motor.objects.filter(equipo=equipo)
        resistencias = Resistencia.objects.filter(equipo=equipo)
        
        return Response({
            'equipo': {
                'id': equipo.id,
                'nombre': equipo.nombre,
                'tipo': equipo.get_tipo_equipo_display(),
            },
            'motores': MotorSerializer(motores, many=True).data,
            'resistencias': ResistenciaSerializer(resistencias, many=True).data,
        })
    
    @action(detail=True, methods=['post'])
    def agregar_motor(self, request, pk=None):
        """
        Agregar un motor a un equipo existente.
        """
        equipo = self.get_object()
        
        serializer = MotorSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(equipo=equipo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def agregar_resistencia(self, request, pk=None):
        """
        Agregar una resistencia a un equipo existente.
        """
        equipo = self.get_object()
        
        serializer = ResistenciaSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(equipo=equipo)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def tipos_disponibles(self, request):
        """
        Obtener información sobre los tipos de equipos disponibles.
        """
        tipos_info = [
            {
                'valor': 'evaporador',
                'display': 'Evaporador',
                'descripcion': 'Intercambiador de calor que evapora el refrigerante',
                'campos_especificos': [
                    {'nombre': 'ancho', 'tipo': 'decimal', 'unidad': 'mm', 'requerido': True},
                    {'nombre': 'alto', 'tipo': 'decimal', 'unidad': 'mm', 'requerido': True},
                    {'nombre': 'profundidad', 'tipo': 'decimal', 'unidad': 'mm', 'requerido': True},
                    {'nombre': 'tipo_evaporador', 'tipo': 'choice', 'opciones': [
                        {'valor': 'aire_forzado', 'display': 'Aire Forzado'},
                        {'valor': 'estatica', 'display': 'Estática'},
                        {'valor': 'cascada', 'display': 'Cascada'},
                        {'valor': 'inundado', 'display': 'Inundado'},
                    ], 'requerido': True},
                ]
            },
            {
                'valor': 'compresor',
                'display': 'Compresor',
                'descripcion': 'Aumenta la presión del refrigerante',
                'campos_especificos': [
                    {'nombre': 'tipo_compresor', 'tipo': 'choice', 'opciones': [
                        {'valor': 'tornillo', 'display': 'Tornillo'},
                        {'valor': 'alternativo', 'display': 'Alternativo'},
                        {'valor': 'scroll', 'display': 'Scroll'},
                        {'valor': 'centrifugo', 'display': 'Centrífugo'},
                    ], 'requerido': True},
                    {'nombre': 'capacidad_refrigeracion', 'tipo': 'decimal', 'unidad': 'TR', 'requerido': True},
                ]
            },
            {
                'valor': 'condensador',
                'display': 'Condensador',
                'descripcion': 'Condensa el refrigerante de vapor a líquido',
                'campos_especificos': [
                    {'nombre': 'tipo_condensador', 'tipo': 'choice', 'opciones': [
                        {'valor': 'aire', 'display': 'Por Aire'},
                        {'valor': 'evaporativo', 'display': 'Evaporativo'},
                        {'valor': 'adiabatico', 'display': 'Adiabático'},
                    ], 'requerido': True},
                    {'nombre': 'capacidad_rechazo_calor', 'tipo': 'decimal', 'unidad': 'kW', 'requerido': True},
                ]
            },
            {
                'valor': 'deshumificador',
                'display': 'Deshumificador',
                'descripcion': 'Controla la humedad del ambiente',
                'campos_especificos': [
                    {'nombre': 'capacidad_extraccion', 'tipo': 'decimal', 'unidad': 'L/día', 'requerido': True},
                    {'nombre': 'caudal_aire', 'tipo': 'decimal', 'unidad': 'm³/h', 'requerido': True},
                ]
            },
            {
                'valor': 'enfriador_glicol',
                'display': 'Enfriador de Glicol',
                'descripcion': 'Sistema de enfriamiento con glicol',
                'campos_especificos': [
                    {'nombre': 'capacidad_refrigeracion', 'tipo': 'decimal', 'unidad': 'kW', 'requerido': True},
                    {'nombre': 'caudal_glicol', 'tipo': 'decimal', 'unidad': 'L/min', 'requerido': True},
                ]
            },
            {
                'valor': 'ventilador',
                'display': 'Ventilador',
                'descripcion': 'Sistema de circulación de aire',
                'campos_especificos': [
                    {'nombre': 'tipo_ventilador', 'tipo': 'choice', 'opciones': [
                        {'valor': 'axial', 'display': 'Axial'},
                        {'valor': 'centrifugo', 'display': 'Centrífugo'},
                        {'valor': 'helicoidal', 'display': 'Helicoidal'},
                    ], 'requerido': True},
                    {'nombre': 'caudal_aire', 'tipo': 'decimal', 'unidad': 'm³/h', 'requerido': True},
                ]
            },
            {
                'valor': 'bomba_glicol',
                'display': 'Bomba de Glicol',
                'descripcion': 'Bombea el glicol en el sistema',
                'campos_especificos': [
                    {'nombre': 'tipo_bomba', 'tipo': 'choice', 'opciones': [
                        {'valor': 'centrifuga', 'display': 'Centrífuga'},
                        {'valor': 'piston', 'display': 'Pistón'},
                        {'nombre': 'diafragma', 'display': 'Diafragma'},
                        {'nombre': 'tornillo', 'display': 'Tornillo'},
                    ], 'requerido': True},
                    {'nombre': 'caudal_nominal', 'tipo': 'decimal', 'unidad': 'L/min', 'requerido': True},
                ]
            },
        ]
        
        return Response({
            'tipos': tipos_info,
            'componentes_electricos': {
                'motores': {
                    'fases': Motor.FASES,
                },
                'resistencias': {
                    'tipos': Resistencia.TIPOS_RESISTENCIA,
                }
            }
        })
    
    @action(detail=False, methods=['get'])
    def estadisticas(self, request):
        """
        Obtener estadísticas generales de todos los equipos.
        """
        user = request.user
        queryset = self.get_queryset()
        
        # Estadísticas generales
        estadisticas = {
            'total_equipos': queryset.count(),
            'por_tipo': {},
            'potencia_total': {
                'watts': 0,
                'kilowatts': 0,
            },
            'consumo_total': {
                'amperios': 0,
            },
            'por_cuarto_frio': {},
        }
        
        # Calcular estadísticas por tipo
        for equipo in queryset:
            # Por tipo
            tipo = equipo.tipo_equipo
            if tipo not in estadisticas['por_tipo']:
                estadisticas['por_tipo'][tipo] = {
                    'cantidad': 0,
                    'potencia_total_w': 0,
                    'consumo_total_a': 0,
                }
            
            estadisticas['por_tipo'][tipo]['cantidad'] += 1
            
            # Por cuarto frío
            cold_room_id = equipo.cold_room.id
            cold_room_nombre = equipo.cold_room.nombre_cuarto
            
            if cold_room_id not in estadisticas['por_cuarto_frio']:
                estadisticas['por_cuarto_frio'][cold_room_id] = {
                    'nombre': cold_room_nombre,
                    'cantidad_equipos': 0,
                    'potencia_total_w': 0,
                    'consumo_total_a': 0,
                }
            
            estadisticas['por_cuarto_frio'][cold_room_id]['cantidad_equipos'] += 1
            
            # Sumar potencias y consumos
            if hasattr(equipo, 'potencia_total'):
                potencia_w = equipo.potencia_total.get('total', {}).get('watts', 0)
                estadisticas['potencia_total']['watts'] += potencia_w
                estadisticas['potencia_total']['kilowatts'] += equipo.potencia_total.get('total', {}).get('kilowatts', 0)
                
                # Acumular por tipo
                estadisticas['por_tipo'][tipo]['potencia_total_w'] += potencia_w
                
                # Acumular por cuarto frío
                estadisticas['por_cuarto_frio'][cold_room_id]['potencia_total_w'] += potencia_w
            
            if hasattr(equipo, 'consumo_total'):
                consumo_a = equipo.consumo_total.get('total_amperios', 0)
                estadisticas['consumo_total']['amperios'] += consumo_a
                
                # Acumular por tipo
                estadisticas['por_tipo'][tipo]['consumo_total_a'] += consumo_a
                
                # Acumular por cuarto frío
                estadisticas['por_cuarto_frio'][cold_room_id]['consumo_total_a'] += consumo_a
        
        return Response(estadisticas)


class MotorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar motores de manera independiente.
    """
    serializer_class = MotorSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Motor.objects.all()
        
        # Filtrar por permisos
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(equipo__cold_room__presupuesto__creado_por=user) |
                Q(equipo__cold_room__presupuesto__ingeniero_responsable=user)
            )
        
        # Filtrar por equipo si se especifica
        equipo_id = self.request.query_params.get('equipo_id')
        if equipo_id:
            queryset = queryset.filter(equipo_id=equipo_id)
        
        return queryset.select_related('equipo', 'equipo__cold_room')


class ResistenciaViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar resistencias de manera independiente.
    """
    serializer_class = ResistenciaSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Resistencia.objects.all()
        
        # Filtrar por permisos
        if not user.is_superuser:
            queryset = queryset.filter(
                Q(equipo__cold_room__presupuesto__creado_por=user) |
                Q(equipo__cold_room__presupuesto__ingeniero_responsable=user)
            )
        
        # Filtrar por equipo si se especifica
        equipo_id = self.request.query_params.get('equipo_id')
        if equipo_id:
            queryset = queryset.filter(equipo_id=equipo_id)
        
        return queryset.select_related('equipo', 'equipo__cold_room')