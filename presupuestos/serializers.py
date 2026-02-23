from rest_framework import serializers
from .models import Presupuesto, Especialidad, PermisoPresupuesto
from django.contrib.auth import get_user_model

User = get_user_model()

class EspecialidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Especialidad
        fields = ['id', 'nombre']

class PresupuestoSerializer(serializers.ModelSerializer):
    # Para lectura: mostrar nombre completo del ingeniero
    ingeniero_responsable_nombre = serializers.CharField(
        source='ingeniero_responsable.get_full_name',
        read_only=True
    )
    
    # Para lectura: ID del ingeniero para formularios de edición
    ingeniero_responsable_id = serializers.IntegerField(
        source='ingeniero_responsable.id',
        read_only=True
    )
    
    # Para escritura: aceptar ID de usuario
    ingeniero_responsable = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False  # No requerido, se usará el usuario actual si no se proporciona
    )
    
    # Mostrar detalles de especialidades (renombrado a _detalle para consistencia con frontend)
    especialidades_detalle = EspecialidadSerializer(
        source='especialidades',
        many=True,
        read_only=True
    )
    
    # Para escritura: aceptar lista de IDs de especialidades
    especialidades = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Especialidad.objects.all(),
        write_only=True
    )

    creado_por_username = serializers.CharField(
        source='creado_por.username',
        read_only=True
    )
    
    class Meta:
        model = Presupuesto
        fields = [
            'id',
            'nombre_proyecto',
            'ingeniero_responsable',  # Para escritura (ID)
            'ingeniero_responsable_id', # Para lectura (ID)
            'ingeniero_responsable_nombre',  # Para lectura (nombre)
            'especialidades',  # Para escritura (lista de IDs)
            'especialidades_detalle',  # Para lectura (detalles)
            'fecha_creacion',
            'consecutivo',
            'validez_oferta',
            'tipo_proyecto',
            'formas_pago',
            'cliente',
            'ubicacion_geografica',
            'fecha_ultima_modificacion',
            'version_presupuesto',
            'activo',
            'es_prestamo',
            'presupuesto_padre',
            'dueno_original',
            'creado_por',
            'creado_por_username',
        ]
        read_only_fields = [
            'id', 
            'consecutivo',
            'fecha_creacion', 
            'fecha_ultima_modificacion',
            'creado_por',
            'es_prestamo',
            'presupuesto_padre',
            'dueno_original'
        ]
    
    def create(self, validated_data):
        # Extraer las especialidades del validated_data
        especialidades_data = validated_data.pop('especialidades')
        
        # Crear el presupuesto
        presupuesto = Presupuesto.objects.create(**validated_data)
        
        # Añadir las especialidades (relación ManyToMany)
        presupuesto.especialidades.set(especialidades_data)
        
        return presupuesto
    
class PermisoPresupuestoSerializer(serializers.ModelSerializer):
    usuario_info = serializers.SerializerMethodField()
    presupuesto_info = serializers.SerializerMethodField()
    
    class Meta:
        model = PermisoPresupuesto
        fields = [
            'id', 
            'presupuesto', 
            'presupuesto_info',
            'usuario', 
            'usuario_info',
            'tipo_permiso', 
            'fecha_concesion'
        ]
        read_only_fields = ['fecha_concesion']
    
    def get_usuario_info(self, obj):
        return {
            'id': obj.usuario.id,
            'username': obj.usuario.username,
            'email': obj.usuario.email,
            'full_name': obj.usuario.get_full_name()
        }
    
    def get_presupuesto_info(self, obj):
        return {
            'id': obj.presupuesto.id,
            'consecutivo': obj.presupuesto.consecutivo,
            'nombre_proyecto': obj.presupuesto.nombre_proyecto
        }