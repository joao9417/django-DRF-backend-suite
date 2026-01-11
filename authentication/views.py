from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .serializers import UserRegistrationSerializer, CustomTokenOntainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import Profile


class RegisterUserView(APIView):
    """
    Endpoint para registro de nuevos usuarios.
    
    Crea un usuario y su perfil asociado en el sistema.
    
    ## Campos requeridos:
    
    | Campo | Tipo | Descripción | Ejemplo |
    |-------|------|-------------|---------|
    | username | string | Nombre de usuario único | "juan.perez" |
    | email | string | Correo electrónico válido y único | "juan@empresa.com" |
    | password | string | Contraseña (mín. 8 caracteres, con número y letra) | "MiPass123" |
    | password_confirm | string | Confirmación de contraseña | "MiPass123" |
    | cargo | string | Cargo del usuario en la organización | "Gerente de Proyectos" |
    
    ## Respuestas:
    
    ### 201 Created
    Usuario creado exitosamente.
    ```json
    {
        "username": "juan.perez",
        "email": "juan@empresa.com",
        "message": "Registro exitoso. Usuario creado."
    }
    ```
    
    ### 400 Bad Request
    Error en validación de datos.
    ```json
    {
        "username": ["Este nombre de usuario ya está en uso."],
        "email": ["Este correo electrónico ya está registrado."],
        "password": ["La contraseña debe tener al menos 8 caracteres."]
    }
    ```
    """

    def post(self, request):
        """
        POST /api/v1/register/
        
        Registra un nuevo usuario en el sistema.
        
        Content-Type: application/json
        
        Returns:
            Response: Respuesta con datos del usuario creado o errores de validación
        """

        serializer = UserRegistrationSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user = serializer.save()

        return Response({
            'username': user.username,
            'email': user.email,
            'message': 'Registro exitoso, Usuario creado.'
        }, status=status.HTTP_201_CREATED)

class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint para autenticación de usuarios.
    
    Genera tokens JWT (access y refresh) para usuarios registrados.
    
    ## Campos requeridos:
    
    | Campo | Tipo | Descripción | Ejemplo |
    |-------|------|-------------|---------|
    | username | string | Nombre de usuario | "juan.perez" |
    | password | string | Contraseña del usuario | "MiPass123" |
    
    ## Respuestas:
    
    ### 200 OK
    Autenticación exitosa.
    ```json
    {
        "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        "user": {
            "id": 1,
            "username": "juan.perez",
            "email": "juan@empresa.com"
        }
    }
    ```
    
    ### 401 Unauthorized
    Credenciales inválidas.
    ```json
    {
        "detail": "No active account found with the given credentials"
    }
    ```
    """

    serializer_class = CustomTokenOntainPairSerializer


class UserProfileView(APIView):
    """
    Endpoint para obtener información del perfil del usuario autenticado.
    
    Requiere autenticación mediante token JWT.
    
    ## Headers requeridos:
    
    ```
    Authorization: Bearer <tu_token_jwt>
    ```
    
    ## Respuestas:
    
    ### 200 OK
    Perfil obtenido exitosamente.
    ```json
    {
        "username": "juan.perez",
        "email": "juan@empresa.com",
        "cargo": "Gerente de Proyectos",
        "date_joined": "2024-01-01 10:30:00"
    }
    ```
    
    ### 401 Unauthorized
    Token inválido o no proporcionado.
    ```json
    {
        "detail": "Authentication credentials were not provided."
    }
    ```
    
    ### 404 Not Found
    Perfil no encontrado para el usuario.
    ```json
    {
        "error": "Perfil no encontrado"
    }
    ```
    """
    permission_classes = [IsAuthenticated]  # Solo usuarios autenticados
    
    def get(self, request):
        """
        GET /api/v1/profile/
        
        Obtiene los datos del perfil del usuario actualmente autenticado.
        
        Headers:
            Authorization: Bearer <token_jwt>
        
        Returns:
            Response: Datos del usuario y su perfil
        """
        try:
            profile = Profile.objects.get(user=request.user)
            return Response({
                'username': request.user.username,
                'email': request.user.email,
                'cargo': profile.cargo,
                'date_joined': request.user.date_joined
            })
        except Profile.DoesNotExist:
            return Response({
                'error': 'Perfil no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)