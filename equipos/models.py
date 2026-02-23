from django.db import models
from django.core.validators import MinValueValidator
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from coldrooms.models import ColdRoom

# ==================== COMPONENTES REUTILIZABLES ====================

class ComponenteElectrico(models.Model):
    """Clase base abstracta para componentes eléctricos"""
    nombre = models.CharField(
        max_length=50, 
        help_text="Ej: Motor ventilador 1, Resistencia de descongelación"
    )
    tension = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        verbose_name="Tensión (V)"
    )
    consumo_amperios = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        verbose_name="Consumo (A)"
    )
    potencia_watts = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        verbose_name="Potencia (W)"
    )
    
    class Meta:
        abstract = True


class Motor(ComponenteElectrico):
    """Modelo concreto para motores"""
    FASES = [
        ('monofasico', 'Monofásico (1φ)'),
        ('bifasico', 'Bifásico (2φ)'),
        ('trifasico', 'Trifásico (3φ)'),
    ]
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    equipo = GenericForeignKey('content_type', 'object_id')

    fases = models.CharField(
        max_length=20, 
        choices=FASES, 
        default='trifasico'
    )
    
    class Meta:
        verbose_name = "Motor"
        verbose_name_plural = "Motores"
    
    def __str__(self):
        return f"Motor: {self.nombre} - {self.potencia_watts}W"


class Resistencia(ComponenteElectrico):
    """Modelo concreto para resistencias"""
    TIPOS_RESISTENCIA = [
        ('panel', 'Resistencia de Panel'),
        ('bandeja', 'Resistencia de Bandeja'),
        ('deshumificacion', 'Resistencia de Deshumificación'),
        ('calefaccion', 'Resistencia de Calefacción'),
    ]
    
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    equipo = GenericForeignKey('content_type', 'object_id')

    tipo = models.CharField(
        max_length=20, 
        choices=TIPOS_RESISTENCIA,
        verbose_name="Tipo de Resistencia"
    )
    
    class Meta:
        verbose_name = "Resistencia"
        verbose_name_plural = "Resistencias"
    
    def __str__(self):
        return f"Resistencia {self.get_tipo_display()}: {self.nombre}"


# ==================== MODELO BASE DE EQUIPO ====================

class Equipo(models.Model):
    """Modelo base abstracto para todos los equipos"""
    TIPOS_EQUIPO = [
        ('evaporador', 'Evaporador'),
        ('compresor', 'Compresor'),
        ('condensador', 'Condensador'),
        ('enfriador_glicol', 'Enfriador de Glicol'),
        ('deshumificador', 'Deshumificador'),
        ('ventilador', 'Ventilador'),
        ('bomba_glicol', 'Bomba de Glicol'),
    ]
    
    # Relación básica
    cold_room = models.ForeignKey(
        ColdRoom,
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related",
        verbose_name='Cuarto Frío'
    )
    
    # Información básica
    tipo_equipo = models.CharField(
        max_length=30, 
        choices=TIPOS_EQUIPO,
        verbose_name='Tipo de Equipo'
    )
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre del Equipo'
    )
    
    marca = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Marca'
    )
    
    modelo = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='Modelo'
    )
    
    cantidad = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name='Cantidad'
    )
    
    # Metadatos
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    motores = GenericRelation('Motor')
    resistencias = GenericRelation('Resistencia')
    
    class Meta:
        abstract = True
    
    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_equipo_display()})"
    
    
    @property
    def potencia_total(self):
        """Retorna diccionario detallado de potencias"""
        total_motores = 0
        total_resistencias = 0
        
        if hasattr(self, 'motores'):
            total_motores = sum(m.potencia_watts for m in self.motores.all())
        
        if hasattr(self, 'resistencias'):
            total_resistencias = sum(r.potencia_watts for r in self.resistencias.all())
        
        total_general = total_motores + total_resistencias
        
        return {
            'motores': {
                'watts': total_motores,
                'kilowatts': total_motores / 1000 if total_motores else 0,
                'cantidad': self.motores.count() if hasattr(self, 'motores') else 0,
            },
            'resistencias': {
                'watts': total_resistencias,
                'kilowatts': total_resistencias / 1000 if total_resistencias else 0,
                'cantidad': self.resistencias.count() if hasattr(self, 'resistencias') else 0,
                'por_tipo': self._resistencias_por_tipo(),
            },
            'total': {
                'watts': total_general,
                'kilowatts': total_general / 1000 if total_general else 0,
            }
        }
    
    @property
    def consumo_total(self):
        """Retorna diccionario detallado de consumos eléctricos"""
        consumo_motores = 0
        consumo_resistencias = 0
        
        if hasattr(self, 'motores'):
            consumo_motores = sum(m.consumo_amperios for m in self.motores.all())
        
        if hasattr(self, 'resistencias'):
            consumo_resistencias = sum(r.consumo_amperios for r in self.resistencias.all())
        
        total_consumo = consumo_motores + consumo_resistencias
        
        return {
            'motores_amperios': consumo_motores,
            'resistencias_amperios': consumo_resistencias,
            'total_amperios': total_consumo,
        }
    
    def _resistencias_por_tipo(self):
        """Agrupa resistencias por tipo para análisis detallado"""
        if not hasattr(self, 'resistencias'):
            return {}
        
        tipos = {}
        for resistencia in self.resistencias.all():
            tipo = resistencia.get_tipo_display()
            if tipo not in tipos:
                tipos[tipo] = {
                    'cantidad': 0,
                    'potencia_total_w': 0,
                    'consumo_total_a': 0,
                    'resistencias': []
                }
            
            tipos[tipo]['cantidad'] += 1
            tipos[tipo]['potencia_total_w'] += float(resistencia.potencia_watts)
            tipos[tipo]['consumo_total_a'] += float(resistencia.consumo_amperios)
            tipos[tipo]['resistencias'].append({
                'nombre': resistencia.nombre,
                'potencia_w': float(resistencia.potencia_watts),
                'consumo_a': float(resistencia.consumo_amperios),
            })
        
        return tipos
    
    @property
    def resumen_electrico(self):
        """Resumen completo eléctrico del equipo"""
        return {
            'equipo': {
                'id': self.id,
                'nombre': self.nombre,
                'tipo': self.get_tipo_equipo_display(),
            },
            'potencias': self.potencia_total,
            'consumos': self.consumo_total,
            'resistencias_detalle': self._resistencias_por_tipo(),
            'motores_detalle': self._motores_detalle(),
        }
    
    def _motores_detalle(self):
        """Detalle de todos los motores"""
        if not hasattr(self, 'motores'):
            return []
        
        return [
            {
                'nombre': m.nombre,
                'fases': m.get_fases_display(),
                'tension_v': float(m.tension),
                'consumo_a': float(m.consumo_amperios),
                'potencia_w': float(m.potencia_watts),
                'potencia_kw': float(m.potencia_watts) / 1000,
            }
            for m in self.motores.all()
        ]

# ==================== MODELOS ESPECÍFICOS ====================

class Evaporador(Equipo):
    """Modelo específico para evaporadores"""
    TIPOS_EVAPORADOR = [
        ('aire_forzado', 'Aire Forzado'),
        ('estatica', 'Estática'),
        ('cascada', 'Cascada'),
        ('inundado', 'Inundado'),
    ]
    
    # Dimensiones
    ancho = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Ancho (mm)')
    alto = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Alto (mm)')
    profundidad = models.DecimalField(max_digits=8, decimal_places=2, verbose_name='Profundidad (mm)')
    peso = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, verbose_name='Peso (kg)')
    
    # Especificaciones técnicas
    tipo_evaporador = models.CharField(
        max_length=20, 
        choices=TIPOS_EVAPORADOR,
        verbose_name='Tipo de Evaporador'
    )
    
    caudal_aire = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True,  # MODIFICADO: ahora es opcional
        blank=True, # MODIFICADO: ahora es opcional
        verbose_name='Caudal de Aire (m³/h)'
    )
    
    flecha_aire = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True,  # MODIFICADO: ahora es opcional
        blank=True, # MODIFICADO: ahora es opcional
        verbose_name='Flecha de Aire (m)'
    )
    
    temperatura_evaporacion = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name='Temperatura de Evaporación (°C)'
    )
    
    class Meta:
        verbose_name = 'Evaporador'
        verbose_name_plural = 'Evaporadores'


class Compresor(Equipo):
    """Modelo específico para compresores"""
    TIPOS_COMPRESOR = [
        ('tornillo', 'Tornillo'),
        ('alternativo', 'Alternativo'),
        ('scroll', 'Scroll'),
        ('centrifugo', 'Centrífugo'),
    ]
    
    tipo_compresor = models.CharField(
        max_length=20, 
        choices=TIPOS_COMPRESOR,
        verbose_name='Tipo de Compresor'
    )
    
    capacidad_refrigeracion = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name='Capacidad de Refrigeración (TR)'
    )
    
    caudal_refrigerante = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name='Caudal de Refrigerante (kg/h)'
    )
    
    presion_alta = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        verbose_name='Presión Alta (bar)'
    )
    
    presion_baja = models.DecimalField(
        max_digits=6, 
        decimal_places=2,
        verbose_name='Presión Baja (bar)'
    )
    
    class Meta:
        verbose_name = 'Compresor'
        verbose_name_plural = 'Compresores'


class Deshumificador(Equipo):
    """Modelo específico para deshumidificadores"""
    capacidad_extraccion = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name='Capacidad de Extracción (L/día)'
    )
    
    caudal_aire = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name='Caudal de Aire (m³/h)'
    )
    
    temperatura_operacion = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Temperatura de Operación (°C)'
    )
    
    humedad_relativa = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Humedad Relativa (%)'
    )
    
    class Meta:
        verbose_name = 'Deshumificador'
        verbose_name_plural = 'Deshumificadores'


class EnfriadorGlicol(Equipo):
    """Modelo específico para enfriadores de glicol"""
    capacidad_refrigeracion = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name='Capacidad de Refrigeración (kW)'
    )
    
    caudal_glicol = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name='Caudal de Glicol (L/min)'
    )
    
    temperatura_entrada = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Temperatura Entrada (°C)'
    )
    
    temperatura_salida = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Temperatura Salida (°C)'
    )
    
    concentracion_glicol = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Concentración de Glicol (%)'
    )
    
    class Meta:
        verbose_name = 'Enfriador de Glicol'
        verbose_name_plural = 'Enfriadores de Glicol'



class Condensador(Equipo):
    """Modelo específico para condensadores"""
    TIPOS_CONDENSADOR = [
        ('aire', 'Por Aire'),
        ('evaporativo', 'Evaporativo'),
        ('adiabatico', 'Adiabatico'),
    ]
    
    tipo_condensador = models.CharField(
        max_length=20, 
        choices=TIPOS_CONDENSADOR,
        verbose_name='Tipo de Condensador'
    )
    
    capacidad_rechazo_calor = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        verbose_name='Capacidad de Rechazo de Calor (kW)'
    )
    
    temperatura_condensacion = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        verbose_name='Temperatura de Condensación (°C)'
    )
    
    class Meta:
        verbose_name = 'Condensador'
        verbose_name_plural = 'Condensadores'


class Ventilador(Equipo):
    """Modelo específico para ventiladores"""
    TIPOS_VENTILADOR = [
        ('axial', 'Axial'),
        ('centrifugo', 'Centrífugo'),
        ('helicoidal', 'Helicoidal'),
    ]
    
    tipo_ventilador = models.CharField(
        max_length=20,
        choices=TIPOS_VENTILADOR,
        verbose_name='Tipo de Ventilador'
    )
    
    caudal_aire = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Caudal de Aire (m³/h)'
    )
    
    presion_estatica = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Presión Estática (Pa)'
    )
    
    diametro_aspas = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Diámetro de Aspas (mm)'
    )
    
    velocidad_rotacion = models.DecimalField(
        max_digits=6,
        decimal_places=0,
        verbose_name='Velocidad de Rotación (RPM)'
    )
    
    class Meta:
        verbose_name = 'Ventilador'
        verbose_name_plural = 'Ventiladores'


class BombaGlicol(Equipo):
    """Modelo específico para bombas de glicol"""
    TIPOS_BOMBA = [
        ('centrifuga', 'Centrífuga'),
        ('piston', 'Pistón'),
        ('diafragma', 'Diafragma'),
        ('tornillo', 'Tornillo'),
    ]
    
    tipo_bomba = models.CharField(
        max_length=20,
        choices=TIPOS_BOMBA,
        verbose_name='Tipo de Bomba'
    )
    
    caudal_nominal = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Caudal Nominal (L/min)'
    )
    
    presion_trabajo = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Presión de Trabajo (bar)'
    )
    
    altura_elevacion = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        verbose_name='Altura de Elevación (m)'
    )
    
    temperatura_maxima = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name='Temperatura Máxima (°C)'
    )
    
    material_carcasa = models.CharField(
        max_length=50,
        default='Acero Inoxidable',
        verbose_name='Material de Carcasa'
    )
    
    class Meta:
        verbose_name = 'Bomba de Glicol'
        verbose_name_plural = 'Bombas de Glicol'