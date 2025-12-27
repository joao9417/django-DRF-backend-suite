from rest_framework import serializers
from .models import Presupuesto, Especialidad
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
    
    # Para escritura: aceptar ID de usuario
    ingeniero_responsable = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        write_only=True,
        required=False  # No requerido, se usará el usuario actual si no se proporciona
    )
    
    # Mostrar detalles de especialidades
    especialidades_info = EspecialidadSerializer(
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
    
    class Meta:
        model = Presupuesto
        fields = [
            'id',
            'nombre_proyecto',
            'ingeniero_responsable',  # Para escritura (ID)
            'ingeniero_responsable_nombre',  # Para lectura (nombre)
            'especialidades',  # Para escritura (lista de IDs)
            'especialidades_info',  # Para lectura (detalles)
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
        ]
        read_only_fields = [
            'id', 
            'fecha_creacion', 
            'fecha_ultima_modificacion',
            'creado_por'
        ]
    
    def create(self, validated_data):
        # Extraer las especialidades del validated_data
        especialidades_data = validated_data.pop('especialidades')
        
        # Crear el presupuesto
        presupuesto = Presupuesto.objects.create(**validated_data)
        
        # Añadir las especialidades (relación ManyToMany)
        presupuesto.especialidades.set(especialidades_data)
        
        return presupuesto