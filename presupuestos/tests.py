from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
from .models import Presupuesto, Especialidad, PermisoPresupuesto

class PresupuestoPermissionsTests(TestCase):
    def setUp(self):
        print("\n" + "="*50)
        print(f"Configurando: {self._testMethodName}")
        print("="*50)

        self.client = APIClient()
        self.creador = User.objects.create_user('creador', 'creador@test.com', 'pass123')
        self.usuario1 = User.objects.create_user('usuario1', 'user1@test.com', 'pass123')
        self.usuario2 = User.objects.create_user('usuario2', 'user2@test.com', 'pass123')
        
        # Crear especialidad
        self.especialidad = Especialidad.objects.create(nombre='Electricidad')
        
        # Crear presupuesto
        self.presupuesto = Presupuesto.objects.create(
            nombre_proyecto='Proyecto Test',
            ingeniero_responsable=self.creador,
            consecutivo='TEST-001',
            validez_oferta='2024-12-31',
            tipo_proyecto='cotizacion',
            formas_pago='Contado',
            cliente='Cliente Test',
            ubicacion_geografica='Bogotá',
            creado_por=self.creador
        )
        self.presupuesto.especialidades.add(self.especialidad)
        print(f"Entorno listo: Presupuesto ID {self.presupuesto.consecutivo} creado.")
    
    def test_creador_puede_ver_su_presupuesto(self):
        """El creador puede ver su propio presupuesto"""
        print("ejecutando test_creador_puede_ver_su_presupuesto")

        self.client.force_authenticate(user=self.creador)
        print(f"  - Autenticado como: {self.creador.username} (Creador)")

        response = self.client.get(f'/api/v1/presupuestos/presupuestos/{self.presupuesto.id}/')
        print(f"  - Status Code recibido: {response.status_code}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("RESULTADO: OK - El creador tiene acceso.")
    
    def test_usuario_sin_permiso_no_puede_ver(self):
        """Usuario sin permiso no puede ver el presupuesto"""
        print("EJECUTANDO: test_usuario_sin_permiso_no_puede_ver")

        self.client.force_authenticate(user=self.usuario1)
        print(f"  - Autenticado como: {self.usuario1.username} (Sin permiso)")

        response = self.client.get(f'/api/v1/presupuestos/presupuestos/{self.presupuesto.id}/')
        print(f"  - Status Code recibido: {response.status_code}")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("RESULTADO: OK - Acceso denegado correctamente (404).")
    
    def test_compartir_presupuesto(self):
        """El creador puede compartir el presupuesto"""
        print("EJECUTANDO: test_compartir_presupuesto")

        self.client.force_authenticate(user=self.creador)
        print(f"  - Paso 1: {self.creador.username} intenta compartir con {self.usuario1.username}")
        
        data = {
            'usuario_id': self.usuario1.id,
            'tipo_permiso': 'lectura'
        }
        
        response = self.client.post(
            f'/api/v1/presupuestos/presupuestos/{self.presupuesto.id}/compartir/',
            data
        )
        print(f"  - Status Compartir: {response.status_code}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verificar que el usuario ahora puede ver el presupuesto
        print(f"  - Paso 2: Verificando acceso para {self.usuario1.username}...")
        self.client.force_authenticate(user=self.usuario1)
        response = self.client.get(f'/api/v1/presupuestos/presupuestos/{self.presupuesto.id}/')
        print(f"  - Status Verificación: {response.status_code}")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        print("RESULTADO: OK - Presupuesto compartido y accesible.")
    
    def test_no_creador_no_puede_compartir(self):
        """Usuario que no es creador no puede compartir"""
        print("EJECUTANDO: test_no_creador_no_puede_compartir")

        self.client.force_authenticate(user=self.usuario1)
        print(f"  - Autenticado como: {self.usuario1.username} (No es el dueño)")
        
        data = {
            'usuario_id': self.usuario2.id,
            'tipo_permiso': 'lectura'
        }
        
        response = self.client.post(
            f'/api/v1/presupuestos/presupuestos/{self.presupuesto.id}/compartir/',
            data
        )
        print(f"  - Status Code recibido: {response.status_code}")
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        print("RESULTADO: OK - Intento de compartir bloqueado correctamente.")
    
    
    def test_usuario_con_permiso_escritura_puede_editar(self):
        """Usuario con permiso 'escritura' puede editar el presupuesto"""
        print("\nDEBUG: Iniciando test_usuario_con_permiso_escritura_puede_editar")

        from presupuestos.models import PermisoPresupuesto
        print(f"DEBUG: PermisoPresupuesto importado: {PermisoPresupuesto}")

        # Compartir con permiso escritura
        permiso = PermisoPresupuesto.objects.create(
            presupuesto=self.presupuesto,
            usuario=self.usuario1,
            tipo_permiso='escritura'
        )
        print(f"DEBUG: Permiso creado: {permiso}")
        
        self.client.force_authenticate(user=self.usuario1)
        print(f"DEBUG: Usuario autenticado: {self.usuario1.username}")
        
        update_data = {
            'nombre_proyecto': 'Proyecto Actualizado',
            'especialidades': [self.especialidad.id],
            'cliente': 'Cliente Modificado',
            'consecutivo': 'TEST-001',  # Mantener mismo consecutivo
            'validez_oferta': '2024-12-31',
            'tipo_proyecto': 'cotizacion',
            'formas_pago': 'Contado',
            'ubicacion_geografica': 'Bogotá'
        }

        print(f"DEBUG: Enviando PUT a /api/v1/presupuestos/presupuestos/{self.presupuesto.id}/")
        
        response = self.client.put(
            f'/api/v1/presupuestos/presupuestos/{self.presupuesto.id}/',
            update_data,
            format='json'
        )

        print(f"DEBUG: Status code: {response.status_code}")
        print(f"DEBUG: Response content: {response.content}")
        
        # Debería poder editar (200 OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.presupuesto.refresh_from_db()
        self.assertEqual(self.presupuesto.nombre_proyecto, 'Proyecto Actualizado')
    

    def test_usuario_con_permiso_lectura_no_puede_editar(self): 
        """Usuario con permiso 'lectura' NO puede editar"""
        # Compartir con permiso lectura
        PermisoPresupuesto.objects.create(
            presupuesto=self.presupuesto,
            usuario=self.usuario1,
            tipo_permiso='lectura'
        )
        
        self.client.force_authenticate(user=self.usuario1)
        
        update_data = {
            'nombre_proyecto': 'Intento de edición',
            'especialidades': [self.especialidad.id],
            'cliente': 'Cliente Test',
            'consecutivo': 'TEST-001',
            'validez_oferta': '2024-12-31',
            'tipo_proyecto': 'cotizacion',
            'formas_pago': 'Contado',
            'ubicacion_geografica': 'Bogotá'
        }
        
        response = self.client.put(
            f'/api/v1/presupuestos/presupuestos/{self.presupuesto.id}/',
            update_data,
            format='json'
        )
        
        # Debería recibir 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    
    def test_ingeniero_responsable_no_puede_editar(self):
        """Ingeniero responsable NO puede editar (solo lectura)"""
        # Cambiar ingeniero responsable al usuario1
        self.presupuesto.ingeniero_responsable = self.usuario1
        self.presupuesto.save()
        
        self.client.force_authenticate(user=self.usuario1)
        
        update_data = {
            'nombre_proyecto': 'Intento de edición',
            'especialidades': [self.especialidad.id],
            'cliente': 'Cliente Test',
            'consecutivo': 'TEST-001',
            'validez_oferta': '2024-12-31',
            'tipo_proyecto': 'cotizacion',
            'formas_pago': 'Contado',
            'ubicacion_geografica': 'Bogotá'
        }
        
        response = self.client.put(
            f'/api/v1/presupuestos/presupuestos/{self.presupuesto.id}/',
            update_data,
            format='json'
        )
        
        # Debería recibir 403 Forbidden
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
       
    
