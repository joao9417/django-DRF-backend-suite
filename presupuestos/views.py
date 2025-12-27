from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Presupuesto
from .serializers import PresupuestoSerializer

class PresupuestoViewSet(viewsets.ModelViewSet):
    queryset = Presupuesto.objects.filter(activo=True)
    serializer_class = PresupuestoSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        # Asignar creador automáticamente
        serializer.save(creado_por=self.request.user)
    
    def get_queryset(self):
        # Opcional: filtrar por usuario si es necesario
        queryset = super().get_queryset()
        
        # Si el usuario no es superusuario, mostrar solo sus presupuestos
        if not self.request.user.is_superuser:
            queryset = queryset.filter(
                creado_por=self.request.user
            ) | queryset.filter(
                ingeniero_responsable=self.request.user
            )
        
        return queryset.distinct()
    
    @action(detail=False, methods=['post'])
    def crear_presupuesto(self, request):
        """Endpoint específico para crear presupuesto desde el formulario"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return Response(
                {
                    'id': serializer.instance.id, 
                    'consecutivo': serializer.instance.consecutivo,
                    'message': 'Presupuesto creado exitosamente'
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)