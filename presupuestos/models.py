from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model

user = get_user_model()

# creo modelo Especialidad para manejar las especialidades de los proyectos

class Especialidad(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    
    class Meta:
        verbose_name_plural = "Especialidades"
    
    def __str__(self):
        return self.nombre
    

# creo modelo Presupuesto para manejar los presupuestos de los proyectos

class Presupuesto(models.Model):
    
    TIPO_PROYECTO = [
        ('pliego', 'Proyecto de Pliego'),
        ('cotizacion', 'Cotización'),
    ]
    
    especialidades = models.ManyToManyField(
        Especialidad,
        related_name='presupuestos_relacionados',
        help_text='Seleccione las especialidades relacionadas con este presupuesto.'
        )
    
    # campos del formulario
    nombre_proyecto = models.CharField(max_length=200)
    ingeniero_responsable = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='presupuestos'
    )
    
    
    fecha_creacion = models.DateField(auto_now_add=True)
    
    consecutivo = models.CharField(max_length=50, unique=True)
    
    validez_oferta = models.DateField()
    
    tipo_proyecto = models.CharField(max_length=20, choices=TIPO_PROYECTO)
    
    formas_pago = models.TextField()
    
    cliente = models.CharField(max_length=200)
    
    ubicacion_geografica = models.CharField(max_length=300)
    
    fecha_ultima_modificacion = models.DateTimeField(auto_now=True)
    
    version_presupuesto = models.CharField(max_length=20, default='1.0')
    
    activo = models.BooleanField(default=True)
    
    creado_por = models.ForeignKey(
        user,
        on_delete=models.SET_NULL,
        null=True,
        related_name='presupuestos_creados'
    )
    
    class Meta:
        ordering = ['-fecha_creacion']
        
    def __str__(self):
            return f"{self.consecutivo} - {self.nombre_proyecto}"
    
    