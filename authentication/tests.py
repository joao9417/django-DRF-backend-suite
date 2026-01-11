from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Profile

class AuthTests(TestCase):
    def setUp(self):
        """
        Configuración inicial que se ejecuta antes de cada test
        """
        self.client = APIClient()
        
        self.register_url = '/api/v1/register/'
        self.login_url = '/api/v1/login/'
        self.profile_url = '/api/v1/profile/'
        self.refresh_url = '/api/v1/token/refresh/'
        
    def test_user_registration(self):
        """
        Test 1: Registrar un nuevo usuario exitosamente
        """
        print("Ejecutando test: Registro de usuario...")
        print(f"   URL usada: {self.register_url}")
        
        data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'TestPass123',
            'password_confirm': 'TestPass123',
            'cargo': 'Analista'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        print(f"   Código recibido: {response.status_code}")
        print(f"   Datos recibidos: {response.data}")
        
        # Verificar que la respuesta es 201 (CREATED)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        print(f"   ✓ Código de estado: {response.status_code} (esperado: 201)")
        
        # Verificar que el usuario se creó en la base de datos
        user_exists = User.objects.filter(username='testuser').exists()
        self.assertTrue(user_exists)
        print(f"   ✓ Usuario 'testuser' creado en BD: {user_exists}")
        
        # Verificar que el perfil se creó con el cargo correcto
        user = User.objects.get(username='testuser')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.cargo, 'Analista')
        print(f"   ✓ Perfil creado con cargo 'Analista': {profile.cargo == 'Analista'}")
        
        # Verificar la estructura de la respuesta
        self.assertIn('username', response.data)
        self.assertIn('email', response.data)
        self.assertIn('message', response.data)
        print(f"   ✓ Respuesta contiene campos esperados: OK")
        
        print("✅ Test de registro COMPLETADO\n")
    
    def test_registration_with_weak_password(self):
        """
        Test 2: Intentar registro con contraseña débil
        """
        print("Ejecutando test: Validación de contraseña débil...")
        
        data = {
            'username': 'user2',
            'email': 'user2@example.com',
            'password': '123',  # Contraseña muy corta
            'password_confirm': '123',
            'cargo': 'Analista'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        print(f"   Código recibido: {response.status_code}")
        print(f"   Error recibido: {response.data}")
        
        # Debe devolver 400 (BAD REQUEST)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print(f"   ✓ Código de estado: {response.status_code} (esperado: 400)")
        
        # Debe contener error de contraseña
        self.assertIn('password', response.data)
        print(f"   ✓ Mensaje de error: {response.data.get('password')}")
        
        print("✅ Test de contraseña débil COMPLETADO\n")
    
    def test_login_success(self):
        """
        Test 3: Login exitoso con usuario registrado
        """
        print("Ejecutando test: Login exitoso...")
        
        # Primero crear el usuario
        user = User.objects.create_user(
            username='loginuser',
            email='login@example.com',
            password='TestPass123'
        )
        Profile.objects.create(user=user, cargo='Gerente')
        
        # Intentar login
        data = {
            'username': 'loginuser',
            'password': 'TestPass123'
        }
        
        response = self.client.post(self.login_url, data, format='json')
        
        print(f"   Código recibido: {response.status_code}")
        print(f"   Datos recibidos: {response.data}")
        
        # Debe devolver 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"   ✓ Código de estado: {response.status_code} (esperado: 200)")
        
        # Debe contener los tokens
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        print(f"   ✓ Token access recibido: {'access' in response.data}")
        print(f"   ✓ Token refresh recibido: {'refresh' in response.data}")
        
        # Debe contener datos del usuario
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'loginuser')
        print(f"   ✓ Datos de usuario incluidos: {response.data['user']['username']}")
        
        print("✅ Test de login COMPLETADO\n")
    
    def test_get_profile_without_auth(self):
        """
        Test 4: Intentar acceder al perfil sin autenticación
        """
        print("Ejecutando test: Acceso a perfil sin autenticación...")
        
        response = self.client.get(self.profile_url)
        
        print(f"   Código recibido: {response.status_code}")
        
        # Debe devolver 401 (UNAUTHORIZED) o 403
        # Para SimpleJWT normalmente es 401
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        print(f"   ✓ Código de estado: {response.status_code} (esperado: 401)")
        
        print("✅ Test de acceso no autorizado COMPLETADO\n")
    
    def test_get_profile_with_auth(self):
        """
        Test 5: Acceder al perfil con autenticación válida
        """
        print("Ejecutando test: Acceso a perfil con autenticación...")
        
        # Crear usuario y obtener token
        user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='TestPass123'
        )
        Profile.objects.create(user=user, cargo='Desarrollador')
        
        # Login para obtener token
        login_data = {'username': 'profileuser', 'password': 'TestPass123'}
        login_response = self.client.post(self.login_url, login_data, format='json')
        
        print(f"   Código de login: {login_response.status_code}")
        
        # Verifica que el login fue exitoso antes de continuar
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        
        access_token = login_response.data['access']
        
        # Hacer request al perfil con token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(self.profile_url)
        
        print(f"   Código de perfil: {response.status_code}")
        print(f"   Datos de perfil: {response.data}")
        
        # Debe devolver 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print(f"   ✓ Código de estado: {response.status_code} (esperado: 200)")
        
        # Verificar datos del perfil
        self.assertEqual(response.data['username'], 'profileuser')
        self.assertEqual(response.data['cargo'], 'Desarrollador')
        print(f"   ✓ Usuario correcto: {response.data['username']}")
        print(f"   ✓ Cargo correcto: {response.data['cargo']}")
        
        print("✅ Test de perfil con autenticación COMPLETADO\n")

    def test_registration_with_existing_email(self):
        """
        Test 6: Intentar registrar usuario con email ya existente
        """
        print("Ejecutando test: Validación de email duplicado...")
        
        # Crear usuario primero
        User.objects.create_user(
            username='user1',
            email='existente@example.com',
            password='TestPass123'
        )
        
        # Intentar crear otro con mismo email
        data = {
            'username': 'user2',
            'email': 'existente@example.com',  # Email duplicado
            'password': 'TestPass123',
            'password_confirm': 'TestPass123',
            'cargo': 'Analista'
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        print(f"   Código recibido: {response.status_code}")
        print(f"   Error recibido: {response.data}")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
        print(f"   ✓ Error de email duplicado: {response.data.get('email')}")
        
        print("✅ Test de email duplicado COMPLETADO\n")
    
    def test_token_refresh(self):
        """
        Test 7: Refrescar token de acceso
        """
        print("Ejecutando test: Refresco de token...")
        
        # Crear usuario y hacer login
        user = User.objects.create_user(
            username='refreshuser',
            email='refresh@example.com',
            password='TestPass123'
        )
        
        # Login para obtener tokens
        login_data = {'username': 'refreshuser', 'password': 'TestPass123'}
        login_response = self.client.post(self.login_url, login_data, format='json')
        
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        refresh_token = login_response.data['refresh']
        
        # Usar refresh token para obtener nuevo access token
        refresh_data = {'refresh': refresh_token}
        refresh_response = self.client.post(self.refresh_url, refresh_data, format='json')
        
        print(f"   Código de refresh: {refresh_response.status_code}")
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)
        print(f"   ✓ Nuevo token access recibido: OK")
        
        print("✅ Test de refresh token COMPLETADO\n")

    
    def test_registration_without_cargo(self):
        """ 
        Test 8: Intentar registro sin especificar cargo
        """

        print("Ejecutando test: Registro sin cargo...")
        
        data = {
            'username': 'usernocargo',
            'email': 'nocargo@example.com',
            'password': 'TestPass123',
            'password_confirm': 'TestPass123',
            # 'cargo': '',  # No enviar cargo
        }
        
        response = self.client.post(self.register_url, data, format='json')
        
        print(f"   Código recibido: {response.status_code}")
        
        # Dependiendo de tu serializer, esto podría ser 400 o 201
        # Si tu serializer requiere cargo, debería ser 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print(f"   ✓ Validación de campo requerido funciona")
        
        print("✅ Test de registro sin cargo COMPLETADO\n")