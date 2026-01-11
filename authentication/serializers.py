from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.models import User
from .models import Profile

#serializador para el registro de usuario
class UserRegistrationSerializer(serializers.Serializer):
    """
    Serializer para registro de usuarios.
    
    Valida y crea nuevos usuarios con sus perfiles asociados.
    
    Attributes:
        username (CharField): Nombre de usuario único (max 150 caracteres)
        email (EmailField): Correo electrónico único
        password (CharField): Contraseña (write-only)
        password_confirm (CharField): Confirmación de contraseña (write-only)
        cargo (CharField): Cargo del usuario (max 50 caracteres)
    """
    
    #campos del modelo user
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    #campo del modelo profile
    cargo = serializers.CharField(max_length=50)

    #1. Validaciones (username unico, coincidencia de contraseñas)
    def validate(self, data):
        #1a. coincidencia de contraseñas (validacion HTTP:400)
        if data['password'] != data.pop('password_confirm'):
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        #1b. Correo unico (validacion HTTP 400)
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                'email': 'Este correo electronico ya esta registrado.'
            })
        #1c. Username unico (validacion HTTP 400)
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({
                'username': 'Este nombre de usuario ya esta en uso.'
            })
        
        #2. Validacion fuerte de contraseña
        password = data['password']

        #validar longitud minima
        if len(password) < 8:
            raise serializers.ValidationError({
                'password': 'La contraseña debe tener al menos 8 caracteres.'
            })
        #validar que tenga al menos un numero
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError({
                'password': 'La contraseña debe contener al menos un numero.'
            })
        #validar que tenga al menos una letra
        if not any(char.isalpha() for char in password):
            raise serializers.ValidationError({
                'password': 'La contraseña debe contener al menos una letra.'
            })
        #validar que tenga al menos una mayuscula
        if not any(char.isupper() for char in password):
            raise serializers.ValidationError({
                'password': 'La contraseña debe contener al menos una letra mayuscula.'
            })
        
        return data
    #3. Creacion de usuario y perfil (crear usuario en BD)
    def create(self, validated_data):
        #extraer el campo cargo antes de crear el objeto user
        cargo = validated_data.pop('cargo')

        #se crea el objeto user con la contraseña hasheada
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'] #create_user se encarga del hashing
        )

        #se crear el objeto profile y vincularlo al nuevo user
        Profile.objects.create(
            user=user,
            cargo=cargo
        )

        return user
    

class CustomTokenOntainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['email'] = user.email

        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)

        data['user'] = {
            'id': self.user.id,
            'username': self.user.username,
            'email': self.user.email,
        }
        return data
    