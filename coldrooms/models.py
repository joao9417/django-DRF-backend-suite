from django.db import models
from presupuestos.models import Presupuesto

class ColdRoom(models.Model):
    # relacion obligatoria con Presupuesto
    presupuesto = models.ForeignKey(
        Presupuesto,
        on_delete=models.CASCADE,
        related_name='cold_rooms'
    )
    
    # identificacion - unico dentro del mismo presupuesto
    nombre_cuarto = models.CharField(max_length=100, help_text="Nombre del cuarto frío")
    
    # requerimiento termico
    temperatura_requerida = models.DecimalField(max_digits=10, decimal_places=2, help_text="Temperatura objetivo en °C")  # °C
    
    # dimensiones fisicas (inputs principales)
    ancho = models.DecimalField(max_digits=10, decimal_places=2, help_text="Ancho en metros")  # m
    largo = models.DecimalField(max_digits=10, decimal_places=2, help_text="Largo en metros")  # m
    alto = models.DecimalField(max_digits=10, decimal_places=2, help_text="Alto en metros")  # m
    
    # campo calculado automaticamente
    volumen = models.DecimalField(max_digits=10, decimal_places=2, help_text="Volumen en metros cúbicos", editable=False)  # m³
    
    # metadatos automaticos
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "cuarto frio"
        verbose_name_plural = "cuartos frios"
        
        constraints = [
            models.UniqueConstraint(
                fields=['presupuesto', 'nombre_cuarto'],
                name='unique_coldroom_per_presupuesto'
            )
        ]
        
    def __str__(self):
        return f"Cuarto en {self.presupuesto} ({self.volumen} m³)"
    
    def save(self, *args, **kwargs):
        # logica para calcular el volumen antes de guardar
        if all([self.ancho, self.largo, self.alto]):
            self.volumen = self.ancho * self.largo * self.alto
        super().save(*args, **kwargs)
  