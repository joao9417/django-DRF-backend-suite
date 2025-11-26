from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserRegistrationSerializer, CustomTokenOntainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView


class RegisterUserView(APIView):
    #Gestiona la creacion de nuevos usuarios y perfiles.

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)

        #si NO es valido (validacion backend)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        #si es valido
        user = serializer.save()

        #devolver respuesta HTTP 201 con datos del usuario (sin contraseña)
        return Response({
            'id': user.username,
            'email': user.email,
            'message': 'Registro exitoso, Usuario creado.'
        }, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenOntainPairSerializer
