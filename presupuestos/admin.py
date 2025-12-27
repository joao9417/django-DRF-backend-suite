from django.contrib import admin
from .models import Presupuesto, Especialidad

@admin.register(Especialidad)
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']
    search_fields = ['nombre']

@admin.register(Presupuesto)
class PresupuestoAdmin(admin.ModelAdmin):
    list_display = [
        'consecutivo', 
        'nombre_proyecto',
        'cliente', 
        'ingeniero_responsable',
        'fecha_creacion'
    ]
    
    list_filter = [
        'tipo_proyecto', 
        'activo',
        'especialidades',  
    ]
    
    search_fields = ['nombre_proyecto', 'consecutivo', 'cliente']
    
    readonly_fields = ['fecha_creacion', 'fecha_ultima_modificacion']
    
    
    filter_horizontal = ['especialidades']