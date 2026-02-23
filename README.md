# Suite Budget API
API backend para sistema de gestión de presupuestos de refrigeracion industrial desarrollada con Django REST Framework.

![Django](https://img.shields.io/badge/Django-5.2-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.16-blue.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-blue.svg)
![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)
![JWT](https://img.shields.io/badge/JWT-Auth-orange.svg)
![CORS](https://img.shields.io/badge/CORS-Enabled-brightgreen.svg)

### Instalacion Rapida
1. Clonar repositorio.
	```bash 
	git clone https://github.com/tuusuario/backend-suite-budget.git
	cd backend-suite-budget
	```
 
 2. Crear entorno virtual
	```bash
	python -m venv venv
	
	Windows
	venv\Scripts\activate.ps1
	    
	Linux/Mac
	source venv/bin/activate
	```
 
3. Instalar dependencias
	```bash
	pip install -r requirements.txt
	```
   
4. Configurar variables de entorno (copia .env.example a .env y edita)
	```bash
	DB_NAME= db_name
	DB_USER= db_user
	DB_PASSWORD= db_password
	DB_HOST= localhost
	DB_PORT= 5432
	```

5. Migrar base de datos y ejecutar
	```bash
	python manage.py migrate
	python manage.py runserver
	```

### Documentacion de la API
- **Swagger UI**: http://localhost:8000/swagger/
- **ReDoc**: http://localhost:8000/redoc/

### Endpoints Principales
**Autenticacion**
- POST /api/v1/register/ - Registrar usuario
- POST /api/v1/login/ - Iniciar sesion (obtener JWT)
- POST /api/v1/token/refresh/ - Refrescar token
- GET /api/v1/profile/ - Ver perfil (requiere autenticacion)

### Ejecutar test
```bash 
	python manage.py test
	python manage.py test authentication #Ejecuta solo el test de authentication
```

### Estructura del Proyecto
```text
		backend-suite-budget/
	├── authentication/      # Sistema de autenticación JWT
	├── presupuestos/       # Gestión de presupuestos
	├── coldrooms/         # Gestión de cuartos fríos
	├── equipos/           # Gestión de equipos
	├── core_project/      # Configuración principal
	├── requirements.txt   # Dependencias
	└── manage.py         # Script de Django
```
