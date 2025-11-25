from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Profile

#serializador para el registro de usuario
#uso Serializer porque se controla manualmente como se crean los datos
class UserRegistrationSerializer(serializers.Serializer):
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
        #1b. correo unico (validacion HTTP 400)
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({
                'email': 'Este correo electronico ya esta registrado.'
            })
        #1c. Username unico (validacion HTTP 400)
        if User.objects.filter(username=data['username']).exists():
            raise serializers.ValidationError({
                'username': 'Este nombre de usuario ya esta en uso.'
            })
        
        #agregar validacion de contraseña fuerte aca...
        return data
    #2. Creacion de usuario y perfil (crear usuario en BD)
    def create(self, validated_data):
        #extraer el campo cargo antes de crear el objeto user
        cargo = validated_data.pop('cargo')

        #se crea el objeto user con la contraseña hasheada
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'] #create_user se encarga del hashing
        )

        #crear el objeto profile y vincularlo al nuevo user
        Profile.objects.create(
            user=user,
            cargo=cargo
        )

        return user
    