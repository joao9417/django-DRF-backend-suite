from django.contrib import admin
from django.contrib.contenttypes.admin import GenericTabularInline
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Evaporador, Compresor, Condensador, Deshumificador, 
    EnfriadorGlicol, Ventilador, BombaGlicol,
    Motor, Resistencia
)

# ==================== INLINES PARA COMPONENTES ELÉCTRICOS ====================

class MotorInline(GenericTabularInline):
    """Inline para mostrar motores en equipos"""
    model = Motor
    extra = 1
    fields = ['nombre', 'tension', 'consumo_amperios', 'potencia_watts', 'fases', 'resumen_electrico']
    readonly_fields = ['resumen_electrico']
    
    def resumen_electrico(self, obj):
        """Mostrar resumen del motor"""
        if obj.id:
            return f"{obj.potencia_watts}W, {obj.tension}V, {obj.get_fases_display()}"
        return "-"
    resumen_electrico.short_description = "Resumen"


class ResistenciaInline(GenericTabularInline):
    """Inline para mostrar resistencias en equipos"""
    model = Resistencia
    extra = 1
    fields = ['nombre', 'tension', 'consumo_amperios', 'potencia_watts', 'tipo', 'resumen_electrico']
    readonly_fields = ['resumen_electrico']
    
    def resumen_electrico(self, obj):
        """Mostrar resumen de la resistencia"""
        if obj.id:
            return f"{obj.potencia_watts}W, {obj.tension}V, {obj.get_tipo_display()}"
        return "-"
    resumen_electrico.short_description = "Resumen"


# ==================== MIXIN COMÚN PARA ADMINS ====================

class EquipoAdminMixin:
    """Mixin con configuraciones comunes para todos los equipos"""
    
    # Configuración común
    inlines = [MotorInline, ResistenciaInline]
    list_per_page = 20
    
    # Campos de solo lectura
    readonly_fields = [
        'creado_en', 'actualizado_en', 'potencia_total_display',
        'consumo_total_display', 'resumen_electrico_display',
        'cold_room_link'
    ]
    
    # Métodos para list_display
    def potencia_total_display(self, obj):
        """Mostrar potencia total formateada"""
        potencia = obj.potencia_total.get('total', {}).get('watts', 0) if hasattr(obj, 'potencia_total') else 0
        return f"{potencia:,.0f} W" if potencia else "-"
    potencia_total_display.short_description = "Potencia Total"
    potencia_total_display.admin_order_field = 'potencia_total'
    
    def consumo_total_display(self, obj):
        """Mostrar consumo total formateado"""
        consumo = obj.consumo_total.get('total_amperios', 0) if hasattr(obj, 'consumo_total') else 0
        return f"{consumo:,.2f} A" if consumo else "-"
    consumo_total_display.short_description = "Consumo Total"
    
    def resumen_electrico_display(self, obj):
        """Mostrar resumen eléctrico"""
        if hasattr(obj, 'resumen_electrico'):
            motores = obj.potencia_total.get('motores', {}).get('cantidad', 0)
            resistencias = obj.potencia_total.get('resistencias', {}).get('cantidad', 0)
            return f"{motores} motores, {resistencias} resistencias"
        return "-"
    resumen_electrico_display.short_description = "Componentes"
    
    def cold_room_link(self, obj):
        """Enlace al cuarto frío"""
        url = reverse('admin:coldrooms_coldroom_change', args=[obj.cold_room.id])
        return format_html('<a href="{}">{}</a>', url, obj.cold_room.nombre_cuarto)
    cold_room_link.short_description = "Cuarto Frío"
    
    def presupuesto_info(self, obj):
        """Información del presupuesto relacionado"""
        presupuesto = obj.cold_room.presupuesto
        url = reverse('admin:presupuestos_presupuesto_change', args=[presupuesto.id])
        return format_html(
            '<a href="{}">{} - {}</a>',
            url,
            presupuesto.consecutivo,
            presupuesto.nombre_proyecto
        )
    presupuesto_info.short_description = "Presupuesto"
    
    def get_queryset(self, request):
        """Optimizar consultas relacionadas"""
        queryset = super().get_queryset(request)
        return queryset.select_related('cold_room', 'cold_room__presupuesto').prefetch_related('motores', 'resistencias')
    
    def get_fieldsets(self, request, obj=None):
        """Estructura común de fieldsets"""
        base_fieldsets = (
            ('Información Básica', {
                'fields': (
                    'cold_room', 'cold_room_link', 'presupuesto_info',
                    'tipo_equipo', 'nombre', 'marca', 'modelo', 'cantidad'
                )
            }),
            ('Resumen Eléctrico', {
                'fields': (
                    'potencia_total_display', 'consumo_total_display',
                    'resumen_electrico_display'
                ),
                'classes': ('collapse',),
            }),
            ('Metadatos', {
                'fields': ('creado_en', 'actualizado_en'),
                'classes': ('collapse',),
            }),
        )
        return base_fieldsets


# ==================== ADMINS ESPECÍFICOS ====================

@admin.register(Evaporador)
class EvaporadorAdmin(EquipoAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo_evaporador_display', 'cold_room_link',
        'caudal_aire_display', 'potencia_total_display', 'creado_en'
    ]
    
    list_filter = ['tipo_evaporador', 'cold_room__presupuesto', 'creado_en']
    
    search_fields = ['nombre', 'marca', 'modelo', 'cold_room__nombre_cuarto']
    
    def tipo_evaporador_display(self, obj):
        return obj.get_tipo_evaporador_display()
    tipo_evaporador_display.short_description = 'Tipo Evaporador'
    tipo_evaporador_display.admin_order_field = 'tipo_evaporador'
    
    def caudal_aire_display(self, obj):
        return f"{obj.caudal_aire:,.0f} m³/h"
    caudal_aire_display.short_description = 'Caudal Aire'
    caudal_aire_display.admin_order_field = 'caudal_aire'
    
    def get_fieldsets(self, request, obj=None):
        base_fieldsets = super().get_fieldsets(request, obj)
        
        evaporador_fieldsets = (
            ('Dimensiones', {
                'fields': ('ancho', 'alto', 'profundidad', 'peso')
            }),
            ('Especificaciones Técnicas', {
                'fields': ('tipo_evaporador', 'caudal_aire', 'flecha_aire', 'temperatura_evaporacion')
            }),
        )
        
        return evaporador_fieldsets + base_fieldsets


@admin.register(Compresor)
class CompresorAdmin(EquipoAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo_compresor_display', 'cold_room_link',
        'capacidad_refrigeracion_display', 'potencia_total_display', 'creado_en'
    ]
    
    list_filter = ['tipo_compresor', 'cold_room__presupuesto', 'creado_en']
    
    search_fields = ['nombre', 'marca', 'modelo', 'cold_room__nombre_cuarto']
    
    def tipo_compresor_display(self, obj):
        return obj.get_tipo_compresor_display()
    tipo_compresor_display.short_description = 'Tipo Compresor'
    
    def capacidad_refrigeracion_display(self, obj):
        return f"{obj.capacidad_refrigeracion:,.1f} TR"
    capacidad_refrigeracion_display.short_description = 'Capacidad'
    
    def get_fieldsets(self, request, obj=None):
        base_fieldsets = super().get_fieldsets(request, obj)
        
        compresor_fieldsets = (
            ('Especificaciones Técnicas', {
                'fields': (
                    'tipo_compresor', 'capacidad_refrigeracion', 'caudal_refrigerante',
                    'presion_alta', 'presion_baja'
                )
            }),
        )
        
        return compresor_fieldsets + base_fieldsets


@admin.register(Condensador)
class CondensadorAdmin(EquipoAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo_condensador_display', 'cold_room_link',
        'capacidad_rechazo_calor_display', 'potencia_total_display', 'creado_en'
    ]
    
    list_filter = ['tipo_condensador', 'cold_room__presupuesto', 'creado_en']
    
    search_fields = ['nombre', 'marca', 'modelo', 'cold_room__nombre_cuarto']
    
    def tipo_condensador_display(self, obj):
        return obj.get_tipo_condensador_display()
    tipo_condensador_display.short_description = 'Tipo Condensador'
    
    def capacidad_rechazo_calor_display(self, obj):
        return f"{obj.capacidad_rechazo_calor:,.1f} kW"
    capacidad_rechazo_calor_display.short_description = 'Rechazo Calor'
    
    def get_fieldsets(self, request, obj=None):
        base_fieldsets = super().get_fieldsets(request, obj)
        
        condensador_fieldsets = (
            ('Especificaciones Técnicas', {
                'fields': ('tipo_condensador', 'capacidad_rechazo_calor', 'temperatura_condensacion')
            }),
        )
        
        return condensador_fieldsets + base_fieldsets


@admin.register(Deshumificador)
class DeshumificadorAdmin(EquipoAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre', 'cold_room_link', 'capacidad_extraccion_display',
        'caudal_aire_display', 'potencia_total_display', 'creado_en'
    ]
    
    list_filter = ['cold_room__presupuesto', 'creado_en']
    
    search_fields = ['nombre', 'marca', 'modelo', 'cold_room__nombre_cuarto']
    
    def capacidad_extraccion_display(self, obj):
        return f"{obj.capacidad_extraccion:,.0f} L/día"
    capacidad_extraccion_display.short_description = 'Extracción'
    
    def caudal_aire_display(self, obj):
        return f"{obj.caudal_aire:,.0f} m³/h"
    caudal_aire_display.short_description = 'Caudal Aire'
    
    def get_fieldsets(self, request, obj=None):
        base_fieldsets = super().get_fieldsets(request, obj)
        
        deshumificador_fieldsets = (
            ('Especificaciones Técnicas', {
                'fields': (
                    'capacidad_extraccion', 'caudal_aire',
                    'temperatura_operacion', 'humedad_relativa'
                )
            }),
        )
        
        return deshumificador_fieldsets + base_fieldsets


@admin.register(EnfriadorGlicol)
class EnfriadorGlicolAdmin(EquipoAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre', 'cold_room_link', 'capacidad_refrigeracion_display',
        'caudal_glicol_display', 'potencia_total_display', 'creado_en'
    ]
    
    list_filter = ['cold_room__presupuesto', 'creado_en']
    
    search_fields = ['nombre', 'marca', 'modelo', 'cold_room__nombre_cuarto']
    
    def capacidad_refrigeracion_display(self, obj):
        return f"{obj.capacidad_refrigeracion:,.1f} kW"
    capacidad_refrigeracion_display.short_description = 'Capacidad'
    
    def caudal_glicol_display(self, obj):
        return f"{obj.caudal_glicol:,.0f} L/min"
    caudal_glicol_display.short_description = 'Caudal Glicol'
    
    def get_fieldsets(self, request, obj=None):
        base_fieldsets = super().get_fieldsets(request, obj)
        
        enfriador_fieldsets = (
            ('Especificaciones Técnicas', {
                'fields': (
                    'capacidad_refrigeracion', 'caudal_glicol',
                    'temperatura_entrada', 'temperatura_salida', 'concentracion_glicol'
                )
            }),
        )
        
        return enfriador_fieldsets + base_fieldsets


@admin.register(Ventilador)
class VentiladorAdmin(EquipoAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo_ventilador_display', 'cold_room_link',
        'caudal_aire_display', 'potencia_total_display', 'creado_en'
    ]
    
    list_filter = ['tipo_ventilador', 'cold_room__presupuesto', 'creado_en']
    
    search_fields = ['nombre', 'marca', 'modelo', 'cold_room__nombre_cuarto']
    
    def tipo_ventilador_display(self, obj):
        return obj.get_tipo_ventilador_display()
    tipo_ventilador_display.short_description = 'Tipo Ventilador'
    
    def caudal_aire_display(self, obj):
        return f"{obj.caudal_aire:,.0f} m³/h"
    caudal_aire_display.short_description = 'Caudal Aire'
    
    def get_fieldsets(self, request, obj=None):
        base_fieldsets = super().get_fieldsets(request, obj)
        
        ventilador_fieldsets = (
            ('Especificaciones Técnicas', {
                'fields': (
                    'tipo_ventilador', 'caudal_aire', 'presion_estatica',
                    'diametro_aspas', 'velocidad_rotacion'
                )
            }),
        )
        
        return ventilador_fieldsets + base_fieldsets


@admin.register(BombaGlicol)
class BombaGlicolAdmin(EquipoAdminMixin, admin.ModelAdmin):
    list_display = [
        'nombre', 'tipo_bomba_display', 'cold_room_link',
        'caudal_nominal_display', 'potencia_total_display', 'creado_en'
    ]
    
    list_filter = ['tipo_bomba', 'material_carcasa', 'cold_room__presupuesto', 'creado_en']
    
    search_fields = ['nombre', 'marca', 'modelo', 'cold_room__nombre_cuarto', 'material_carcasa']
    
    def tipo_bomba_display(self, obj):
        return obj.get_tipo_bomba_display()
    tipo_bomba_display.short_description = 'Tipo Bomba'
    
    def caudal_nominal_display(self, obj):
        return f"{obj.caudal_nominal:,.0f} L/min"
    caudal_nominal_display.short_description = 'Caudal'
    
    def get_fieldsets(self, request, obj=None):
        base_fieldsets = super().get_fieldsets(request, obj)
        
        bomba_fieldsets = (
            ('Especificaciones Técnicas', {
                'fields': (
                    'tipo_bomba', 'caudal_nominal', 'presion_trabajo',
                    'altura_elevacion', 'temperatura_maxima', 'material_carcasa'
                )
            }),
        )
        
        return bomba_fieldsets + base_fieldsets


# ==================== ADMINS PARA COMPONENTES ELÉCTRICOS ====================

@admin.register(Motor)
class MotorAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'equipo_link', 'potencia_watts_display',
        'tension_display', 'fases_display', 'consumo_amperios_display'
    ]
    
    list_filter = ['fases']
    
    search_fields = ['nombre', 'equipo__nombre', 'equipo__cold_room__nombre_cuarto']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('equipo', 'nombre')
        }),
        ('Especificaciones Eléctricas', {
            'fields': ('tension', 'consumo_amperios', 'potencia_watts', 'fases')
        }),
    )
    
    def equipo_link(self, obj):
        """Enlace al equipo relacionado"""
        if obj.equipo:
            # Determinar el modelo específico del equipo
            model_name = obj.equipo._meta.model_name
            app_label = obj.equipo._meta.app_label
            url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.equipo.id])
            return format_html(
                '<a href="{}">{}</a> <small>({})</small>',
                url,
                obj.equipo.nombre,
                obj.equipo.get_tipo_equipo_display()
            )
        return "-"
    equipo_link.short_description = "Equipo"
    equipo_link.admin_order_field = 'equipo__nombre'
    
    def potencia_watts_display(self, obj):
        return f"{obj.potencia_watts:,.0f} W"
    potencia_watts_display.short_description = "Potencia"
    potencia_watts_display.admin_order_field = 'potencia_watts'
    
    def tension_display(self, obj):
        return f"{obj.tension:,.0f} V"
    tension_display.short_description = "Tensión"
    tension_display.admin_order_field = 'tension'
    
    def consumo_amperios_display(self, obj):
        return f"{obj.consumo_amperios:,.2f} A"
    consumo_amperios_display.short_description = "Consumo"
    consumo_amperios_display.admin_order_field = 'consumo_amperios'
    
    def fases_display(self, obj):
        return obj.get_fases_display()
    fases_display.short_description = "Fases"
    fases_display.admin_order_field = 'fases'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        queryset = super().get_queryset(request)
        return queryset.select_related('equipo', 'equipo__cold_room')


@admin.register(Resistencia)
class ResistenciaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'equipo_link', 'tipo_display',
        'potencia_watts_display', 'tension_display', 'consumo_amperios_display'
    ]
    
    list_filter = ['tipo']
    
    search_fields = ['nombre', 'equipo__nombre', 'equipo__cold_room__nombre_cuarto']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('equipo', 'nombre', 'tipo')
        }),
        ('Especificaciones Eléctricas', {
            'fields': ('tension', 'consumo_amperios', 'potencia_watts')
        }),
    )
    
    def equipo_link(self, obj):
        """Enlace al equipo relacionado"""
        if obj.equipo:
            model_name = obj.equipo._meta.model_name
            app_label = obj.equipo._meta.app_label
            url = reverse(f'admin:{app_label}_{model_name}_change', args=[obj.equipo.id])
            return format_html(
                '<a href="{}">{}</a> <small>({})</small>',
                url,
                obj.equipo.nombre,
                obj.equipo.get_tipo_equipo_display()
            )
        return "-"
    equipo_link.short_description = "Equipo"
    equipo_link.admin_order_field = 'equipo__nombre'
    
    def tipo_display(self, obj):
        return obj.get_tipo_display()
    tipo_display.short_description = "Tipo"
    tipo_display.admin_order_field = 'tipo'
    
    def potencia_watts_display(self, obj):
        return f"{obj.potencia_watts:,.0f} W"
    potencia_watts_display.short_description = "Potencia"
    potencia_watts_display.admin_order_field = 'potencia_watts'
    
    def tension_display(self, obj):
        return f"{obj.tension:,.0f} V"
    tension_display.short_description = "Tensión"
    tension_display.admin_order_field = 'tension'
    
    def consumo_amperios_display(self, obj):
        return f"{obj.consumo_amperios:,.2f} A"
    consumo_amperios_display.short_description = "Consumo"
    consumo_amperios_display.admin_order_field = 'consumo_amperios'
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        queryset = super().get_queryset(request)
        return queryset.select_related('equipo', 'equipo__cold_room')


# ==================== CONFIGURACIÓN DEL SITE ADMIN ====================

# Opcional: Personalizar el encabezado del admin
admin.site.site_header = "Sistema de Presupuestos - Refrigeración"
admin.site.site_title = "Admin Presupuestos"
admin.site.index_title = "Administración del Sistema"

# Agrupar modelos relacionados en el admin
# Nota: Django automáticamente agrupa por app, pero podemos personalizar más