from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from datetime import datetime

User = get_user_model()

# se creo modelo Especialidad para manejar las especialidades de los proyectos

class Especialidad(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    
    class Meta:
        verbose_name_plural = "Especialidades"
    
    def __str__(self):
        return self.nombre
    

# se creo modelo Presupuesto para manejar los presupuestos de los proyectos

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
    
    consecutivo = models.CharField(max_length=50, unique=True, blank=True)
    
    validez_oferta = models.DateField()
    
    tipo_proyecto = models.CharField(max_length=20, choices=TIPO_PROYECTO)
    
    formas_pago = models.TextField()
    
    cliente = models.CharField(max_length=200)
    
    ubicacion_geografica = models.CharField(max_length=300)
    
    fecha_ultima_modificacion = models.DateTimeField(auto_now=True)
    
    version_presupuesto = models.CharField(max_length=20, default='1.0')
    
    activo = models.BooleanField(default=True)
    
    creado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='presupuestos_creados'
    )

    # Campos para flujo de prestamo
    es_prestamo = models.BooleanField(default=False)
    
    presupuesto_padre = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='versiones_derivadas',
        help_text='Presupuesto original del cual se derivó este préstamo o versión'
    )
    
    dueno_original = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='presupuestos_prestados',
        help_text='Dueño original del presupuesto si es un préstamo'
    )

    def save(self, *args, **kwargs):
         if not self.consecutivo:
              year = datetime.now().year
              prefix = f"PR-{year}-"

              ultimo_presupuesto = Presupuesto.objects.filter(
                   consecutivo__startswith=prefix
                ).order_by('-consecutivo').first()
              if ultimo_presupuesto:
                   ultimo_numero = int(ultimo_presupuesto.consecutivo.split('-')[-1])
                   nuevo_numero = ultimo_numero + 1
              else:
                   nuevo_numero = 1

              self.consecutivo = f"{prefix}{nuevo_numero:03d}"
         
         super().save(*args, **kwargs)
              
                
    class Meta:
        ordering = ['-fecha_creacion']
        
    def __str__(self):
            return f"{self.consecutivo} - {self.nombre_proyecto}"
    

class PermisoPresupuesto(models.Model):
     TIPOS_PERMISO = [
          ('lectura', 'Solo lectura'),
          ('escritura', 'Lectura y escritura'),
     ]

     presupuesto = models.ForeignKey(
          Presupuesto,
          on_delete=models.CASCADE,
          related_name='permisos_compartidos'
     )

     usuario = models.ForeignKey(
          User,
          on_delete=models.CASCADE,
          related_name='presupuestos_compartidos'
     )

     tipo_permiso = models.CharField(
          max_length=10,
          choices=TIPOS_PERMISO,
          default='lectura'
     )
     fecha_concesion = models.DateTimeField(auto_now_add=True)

     class Meta:
          unique_together = ['presupuesto', 'usuario']
          verbose_name_plural = "permisos de presupuestos"

     def __str__(self):
        return f"{self.usuario} - {self.presupuesto} ({self.tipo_permiso})"
    
    