from django.contrib import admin
from .models import ColdRoom

@admin.register(ColdRoom)
class ColdRoomAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_cuarto',
        'presupuesto',
        'temperatura_requerida',
        'volumen',
        'creado_en',
    ]
    
    list_filter = ['presupuesto', 'creado_en']
    
    search_fields = [
        'nombre_cuarto',
        'presupuesto__nombre_proyecto',
        'presupuesto__consecutivo',
    ]
    
    readonly_fields = ['volumen', 'creado_en', 'actualizado_en']
    
    fieldsets = (
        ('Información Principal', {
            'fields': (
                'presupuesto',
                'nombre_cuarto',
                'temperatura_requerida',
            )
        }),
        ('Dimensiones', {
            'fields': (
                'ancho',
                'largo',
                'alto',
                'volumen',
            )
        }),
        ('Metadatos', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',),
        }),
    )
    
    def get_queryset(self, request):
        """Optimizar consultas relacionadas"""
        queryset = super().get_queryset(request)
        return queryset.select_related('presupuesto')