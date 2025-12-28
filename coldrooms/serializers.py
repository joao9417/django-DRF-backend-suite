from rest_framework import serializers
from django.db import IntegrityError
from .models import ColdRoom
from presupuestos.models import Presupuesto

class ColdRoomSerializer(serializers.ModelSerializer):
    # Información del presupuesto (solo lectura)
    presupuesto_info = serializers.SerializerMethodField(read_only=True)
    
    # Verificación de permisos
    tiene_permisos = serializers.SerializerMethodField(read_only=True)
    
    class Meta:
        model = ColdRoom
        fields = [
            'id',
            'presupuesto',  # Para escritura (ID)
            'presupuesto_info',  # Para lectura (info detallada)
            'nombre_cuarto',
            'temperatura_requerida',
            'ancho',
            'largo',
            'alto',
            'volumen',  # Calculado automáticamente
            'creado_en',
            'actualizado_en',
            'tiene_permisos',
        ]
        read_only_fields = ['id', 'volumen', 'creado_en', 'actualizado_en', 'tiene_permisos']
    
    def get_presupuesto_info(self, obj):
        """Devuelve información básica del presupuesto relacionado"""
        return {
            'id': obj.presupuesto.id,
            'nombre_proyecto': obj.presupuesto.nombre_proyecto,
            'consecutivo': obj.presupuesto.consecutivo,
            'cliente': obj.presupuesto.cliente,
        }
    
    def get_tiene_permisos(self, obj):
        """Verifica si el usuario actual tiene permisos sobre este cuarto frío"""
        request = self.context.get('request')
        if request and request.user:
            user = request.user
            presupuesto = obj.presupuesto
            return (
                user.is_superuser or
                user == presupuesto.creado_por or
                user == presupuesto.ingeniero_responsable
            )
        return False
    
    def validate_presupuesto(self, value):
        """Valida que el usuario tenga acceso al presupuesto"""
        request = self.context.get('request')
        if request and request.user:
            user = request.user
            
            # Verificar permisos sobre el presupuesto
            if not user.is_superuser:
                if value.creado_por != user and value.ingeniero_responsable != user:
                    raise serializers.ValidationError(
                        "No tienes permisos para agregar cuartos fríos a este presupuesto."
                    )
        
        return value
    
    def validate(self, data):
        """Validaciones adicionales"""
        # Validar que las dimensiones sean positivas
        if data.get('ancho') <= 0 or data.get('largo') <= 0 or data.get('alto') <= 0:
            raise serializers.ValidationError(
                "Las dimensiones deben ser valores positivos."
            )
        
        # Validar temperatura razonable (ajustable según necesidades)
        temperatura = data.get('temperatura_requerida')
        if temperatura is not None:
            if temperatura > 15 or temperatura < -50:
                raise serializers.ValidationError(
                    "La temperatura debe estar entre -50°C y 15°C."
                )
        
        # Validar unicidad del nombre dentro del mismo presupuesto
        presupuesto = data.get('presupuesto')
        nombre_cuarto = data.get('nombre_cuarto')
        
        # Solo validar si ambos están presentes
        if presupuesto and nombre_cuarto:
            if self.instance:
                # Si estamos actualizando, excluimos el registro actual
                qs = ColdRoom.objects.filter(
                    presupuesto=presupuesto,
                    nombre_cuarto=nombre_cuarto
                ).exclude(pk=self.instance.pk)
            else:
                # Si estamos creando nuevo
                qs = ColdRoom.objects.filter(
                    presupuesto=presupuesto,
                    nombre_cuarto=nombre_cuarto
                )
            
            if qs.exists():
                raise serializers.ValidationError({
                    'nombre_cuarto': 'Ya existe un cuarto frío con este nombre en el presupuesto seleccionado.'
                })
        
        return data
    
    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            # Capturar error de unicidad de base de datos
            if 'unique_coldroom_name_per_presupuesto' in str(e):
                raise serializers.ValidationError({
                    'non_field_errors': [
                        'Ya existe un cuarto frío con este nombre en el presupuesto seleccionado.'
                    ]
                })
            raise