from rest_framework import serializers
from django.db import transaction
from .models import (
    Evaporador, Compresor, Condensador, Deshumificador, 
    EnfriadorGlicol, Ventilador, BombaGlicol,
    Motor, Resistencia
)

# ==================== SERIALIZERS DE COMPONENTES ====================

class MotorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Motor
        fields = ['id', 'nombre', 'tension', 'consumo_amperios', 'potencia_watts', 'fases']
        read_only_fields = ['id']

class ResistenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resistencia
        fields = ['id', 'nombre', 'tension', 'consumo_amperios', 'potencia_watts', 'tipo']
        read_only_fields = ['id']

# ==================== MIXIN COMÚN PARA SERIALIZERS ====================

class EquipoSerializerMixin:
    """Mixin con campos y métodos comunes para todos los serializers de equipos"""
    
    potencia_total = serializers.SerializerMethodField()
    consumo_total = serializers.SerializerMethodField()
    resumen_electrico = serializers.SerializerMethodField()
    cold_room_info = serializers.SerializerMethodField()
    
    def get_potencia_total(self, obj):
        return obj.potencia_total if hasattr(obj, 'potencia_total') else {}
    
    def get_consumo_total(self, obj):
        return obj.consumo_total if hasattr(obj, 'consumo_total') else {}
    
    def get_resumen_electrico(self, obj):
        return obj.resumen_electrico if hasattr(obj, 'resumen_electrico') else {}
    
    def get_cold_room_info(self, obj):
        # Importación local para evitar importación circular
        from coldrooms.serializers import ColdRoomSerializer
        cold_room = obj.cold_room
        if cold_room:
            return ColdRoomSerializer(cold_room, context=self.context).data
        return None
    
    def create_with_components(self, validated_data, equipo_class):
        """Lógica centralizada para crear equipo + motores + resistencias"""
        motores_data = validated_data.pop('motores', [])
        resistencias_data = validated_data.pop('resistencias', [])
        
        with transaction.atomic():
            equipo = equipo_class.objects.create(**validated_data)
            
            for motor_data in motores_data:
                Motor.objects.create(equipo=equipo, **motor_data)
            
            for resistencia_data in resistencias_data:
                Resistencia.objects.create(equipo=equipo, **resistencia_data)
            
            return equipo

    def update_with_components(self, instance, validated_data):
        """Lógica centralizada para actualizar equipo y sus componentes"""
        motores_data = validated_data.pop('motores', None)
        resistencias_data = validated_data.pop('resistencias', None)
        
        with transaction.atomic():
            for attr, value in validated_data.items():
                setattr(instance, attr, value)
            instance.save()
            
            if motores_data is not None:
                instance.motores.all().delete()
                for m_data in motores_data:
                    Motor.objects.create(equipo=instance, **m_data)
            
            if resistencias_data is not None:
                instance.resistencias.all().delete()
                for r_data in resistencias_data:
                    Resistencia.objects.create(equipo=instance, **r_data)
                    
        return instance

# ==================== SERIALIZERS ESPECÍFICOS ====================

class EvaporadorSerializer(EquipoSerializerMixin, serializers.ModelSerializer):
    motores = MotorSerializer(many=True, required=False)
    resistencias = ResistenciaSerializer(many=True, required=False)
    
    class Meta:
        model = Evaporador
        fields = [
            'id', 'cold_room', 'tipo_equipo', 'nombre', 'marca', 'modelo', 
            'cantidad', 'ancho', 'alto', 'profundidad', 'peso', 'tipo_evaporador',
            'caudal_aire', 'flecha_aire', 'temperatura_evaporacion', 'motores', 
            'resistencias', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
    
    # FALTA ESTE MÉTODO:
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['potencia_total'] = self.get_potencia_total(instance)
        representation['consumo_total'] = self.get_consumo_total(instance)
        representation['resumen_electrico'] = self.get_resumen_electrico(instance)
        representation['cold_room_info'] = self.get_cold_room_info(instance)
        return representation
    
    def create(self, validated_data):
        return self.create_with_components(validated_data, Evaporador)
    
    def update(self, instance, validated_data):
        return self.update_with_components(instance, validated_data)

class CompresorSerializer(EquipoSerializerMixin, serializers.ModelSerializer):
    motores = MotorSerializer(many=True, required=False)
    resistencias = ResistenciaSerializer(many=True, required=False)
    
    class Meta:
        model = Compresor
        fields = [
            'id', 'cold_room', 'tipo_equipo', 'nombre', 'marca', 'modelo', 
            'cantidad', 'ancho', 'alto', 'profundidad', 'tipo_compresor', 
            'refrigerante', 'capacidad_btuh', 'capacidad_toneladas', 'motores', 
            'resistencias', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['potencia_total'] = self.get_potencia_total(instance)
        representation['consumo_total'] = self.get_consumo_total(instance)
        representation['resumen_electrico'] = self.get_resumen_electrico(instance)
        representation['cold_room_info'] = self.get_cold_room_info(instance)
        return representation
    
    def create(self, validated_data):
        return self.create_with_components(validated_data, Compresor)
    
    def update(self, instance, validated_data):
        return self.update_with_components(instance, validated_data)

class CondensadorSerializer(EquipoSerializerMixin, serializers.ModelSerializer):
    motores = MotorSerializer(many=True, required=False)
    resistencias = ResistenciaSerializer(many=True, required=False)
    
    class Meta:
        model = Condensador
        fields = [
            'id', 'cold_room', 'tipo_equipo', 'nombre', 'marca', 'modelo', 
            'cantidad', 'ancho', 'alto', 'profundidad', 'tipo_condensador', 
            'caudal_agua', 'presion_agua', 'temperatura_condensacion', 'motores', 
            'resistencias', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['potencia_total'] = self.get_potencia_total(instance)
        representation['consumo_total'] = self.get_consumo_total(instance)
        representation['resumen_electrico'] = self.get_resumen_electrico(instance)
        representation['cold_room_info'] = self.get_cold_room_info(instance)
        return representation
    
    def create(self, validated_data):
        return self.create_with_components(validated_data, Condensador)
    
    def update(self, instance, validated_data):
        return self.update_with_components(instance, validated_data)

class DeshumificadorSerializer(EquipoSerializerMixin, serializers.ModelSerializer):
    motores = MotorSerializer(many=True, required=False)
    resistencias = ResistenciaSerializer(many=True, required=False)
    
    class Meta:
        model = Deshumificador
        fields = [
            'id', 'cold_room', 'tipo_equipo', 'nombre', 'marca', 'modelo', 
            'cantidad', 'ancho', 'alto', 'profundidad', 'capacidad_deshumidificacion', 
            'caudal_aire', 'temperatura_operacion', 'motores', 'resistencias', 
            'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['potencia_total'] = self.get_potencia_total(instance)
        representation['consumo_total'] = self.get_consumo_total(instance)
        representation['resumen_electrico'] = self.get_resumen_electrico(instance)
        representation['cold_room_info'] = self.get_cold_room_info(instance)
        return representation
    
    def create(self, validated_data):
        return self.create_with_components(validated_data, Deshumificador)
    
    def update(self, instance, validated_data):
        return self.update_with_components(instance, validated_data)

class EnfriadorGlicolSerializer(EquipoSerializerMixin, serializers.ModelSerializer):
    motores = MotorSerializer(many=True, required=False)
    resistencias = ResistenciaSerializer(many=True, required=False)
    
    class Meta:
        model = EnfriadorGlicol
        fields = [
            'id', 'cold_room', 'tipo_equipo', 'nombre', 'marca', 'modelo', 
            'cantidad', 'ancho', 'alto', 'profundidad', 'tipo_glicol', 
            'concentracion_glicol', 'caudal_glicol', 'temperatura_entrada', 
            'temperatura_salida', 'motores', 'resistencias', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['potencia_total'] = self.get_potencia_total(instance)
        representation['consumo_total'] = self.get_consumo_total(instance)
        representation['resumen_electrico'] = self.get_resumen_electrico(instance)
        representation['cold_room_info'] = self.get_cold_room_info(instance)
        return representation
    
    def create(self, validated_data):
        return self.create_with_components(validated_data, EnfriadorGlicol)
    
    def update(self, instance, validated_data):
        return self.update_with_components(instance, validated_data)

class VentiladorSerializer(EquipoSerializerMixin, serializers.ModelSerializer):
    motores = MotorSerializer(many=True, required=False)
    resistencias = ResistenciaSerializer(many=True, required=False)
    
    class Meta:
        model = Ventilador
        fields = [
            'id', 'cold_room', 'tipo_equipo', 'nombre', 'marca', 'modelo', 
            'cantidad', 'ancho', 'alto', 'profundidad', 'tipo_ventilador', 
            'caudal_aire', 'presion_estatica', 'diametro_aspas', 'motores', 'resistencias', 
            'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['potencia_total'] = self.get_potencia_total(instance)
        representation['consumo_total'] = self.get_consumo_total(instance)
        representation['resumen_electrico'] = self.get_resumen_electrico(instance)
        representation['cold_room_info'] = self.get_cold_room_info(instance)
        return representation
    
    def create(self, validated_data):
        return self.create_with_components(validated_data, Ventilador)
    
    def update(self, instance, validated_data):
        return self.update_with_components(instance, validated_data)

class BombaGlicolSerializer(EquipoSerializerMixin, serializers.ModelSerializer):
    motores = MotorSerializer(many=True, required=False)
    resistencias = ResistenciaSerializer(many=True, required=False)
    
    class Meta:
        model = BombaGlicol
        fields = [
            'id', 'cold_room', 'tipo_equipo', 'nombre', 'marca', 'modelo', 
            'cantidad', 'ancho', 'alto', 'profundidad', 'tipo_bomba', 
            'caudal_glicol', 'presion_descarga', 'material_carcasa', 'motores', 
            'resistencias', 'creado_en', 'actualizado_en',
        ]
        read_only_fields = ['id', 'creado_en', 'actualizado_en']
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['potencia_total'] = self.get_potencia_total(instance)
        representation['consumo_total'] = self.get_consumo_total(instance)
        representation['resumen_electrico'] = self.get_resumen_electrico(instance)
        representation['cold_room_info'] = self.get_cold_room_info(instance)
        return representation
    
    def create(self, validated_data):
        return self.create_with_components(validated_data, BombaGlicol)
    
    def update(self, instance, validated_data):
        return self.update_with_components(instance, validated_data)

# ==================== SERIALIZER POLIMÓRFICO ====================

class EquipoPolymorphicSerializer(serializers.Serializer):
    """
    Maneja la lógica de despacho. Determina qué equipo crear 
    basándose en el campo 'tipo_equipo'.
    """
    def get_serializer_map(self):
        return {
            'evaporador': EvaporadorSerializer,
            'compresor': CompresorSerializer,
            'condensador': CondensadorSerializer,
            'deshumificador': DeshumificadorSerializer,
            'enfriador_glicol': EnfriadorGlicolSerializer,
            'ventilador': VentiladorSerializer,
            'bomba_glicol': BombaGlicolSerializer,
        }

    def to_representation(self, instance):
        serializer_class = self.get_serializer_map().get(instance.tipo_equipo)
        if not serializer_class:
            return {"id": instance.id, "error": "Tipo no soportado"}
        return serializer_class(instance, context=self.context).data

    def to_internal_value(self, data):
        tipo_equipo = data.get('tipo_equipo')
        if not tipo_equipo:
            raise serializers.ValidationError({'tipo_equipo': 'Este campo es requerido'})
        
        serializer_class = self.get_serializer_map().get(tipo_equipo)
        if not serializer_class:
            raise serializers.ValidationError({'tipo_equipo': 'Tipo no soportado'})
        
        # Validamos usando el serializador específico
        serializer = serializer_class(data=data, context=self.context)
        if serializer.is_valid():
            # Importante: devolvemos también el tipo_equipo para el método create
            validated_data = serializer.validated_data
            validated_data['tipo_equipo'] = tipo_equipo
            return validated_data
        raise serializers.ValidationError(serializer.errors)

    def create(self, validated_data):
        tipo_equipo = validated_data.get('tipo_equipo')
        serializer_class = self.get_serializer_map().get(tipo_equipo)
        # Instanciamos correctamente para ejecutar su método create()
        serializer = serializer_class(context=self.context)
        return serializer.create(validated_data)

    def update(self, instance, validated_data):
        tipo_equipo = instance.tipo_equipo
        serializer_class = self.get_serializer_map().get(tipo_equipo)
        serializer = serializer_class(context=self.context)
        return serializer.update(instance, validated_data)

# ==================== SERIALIZER PARA LISTADO ====================

class EquipoListSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    tipo_equipo = serializers.CharField()
    nombre = serializers.CharField()
    marca = serializers.CharField()
    modelo = serializers.CharField()
    cantidad = serializers.IntegerField()
    cold_room_nombre = serializers.CharField(source='cold_room.nombre_cuarto')
    cold_room_id = serializers.IntegerField(source='cold_room.id')
    potencia_total_w = serializers.SerializerMethodField()
    consumo_total_a = serializers.SerializerMethodField()
    
    def get_potencia_total_w(self, obj):
        return obj.potencia_total.get('total', {}).get('watts', 0) if hasattr(obj, 'potencia_total') else 0
    
    def get_consumo_total_a(self, obj):
        return obj.consumo_total.get('total_amperios', 0) if hasattr(obj, 'consumo_total') else 0