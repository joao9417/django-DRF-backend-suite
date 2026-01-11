# 🏢 Suite Budget API

![Django](https://img.shields.io/badge/Django-4.2-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.14-blue.svg)
![JWT](https://img.shields.io/badge/JWT-Auth-orange.svg)
![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)

**Sistema de Gestión de Presupuestos con API RESTful** - Backend desarrollado en Django REST Framework con autenticación JWT.

## 📑 Tabla de Contenidos
- [✨ Características](#-características)
- [🏗️ Arquitectura](#️-arquitectura)
- [🚀 Instalación](#-instalación)
- [⚙️ Configuración](#️-configuración)
- [🔐 Autenticación](#-autenticación)
- [📚 API Documentation](#-api-documentation)
- [🧪 Testing](#-testing)
- [📁 Estructura del Proyecto](#-estructura-del-proyecto)
- [🔄 Endpoints Principales](#-endpoints-principales)
- [👥 Contribución](#-contribución)
- [📄 Licencia](#-licencia)

## ✨ Características

### 🔐 **Autenticación y Autorización**
- ✅ Registro de usuarios con validación avanzada
- ✅ Login con tokens JWT (access + refresh)
- ✅ Protección de endpoints con permisos
- ✅ Perfiles de usuario personalizados con cargo
- ✅ Refresh automático de tokens

### 📊 **Gestión de Datos**
- ✅ API RESTful completa
- ✅ Serializadores para validación de datos
- ✅ Modelos relacionales optimizados
- ✅ Filtros y búsquedas avanzadas
- ✅ Documentación automática con Swagger

### 🛡️ **Seguridad**
- ✅ Contraseñas hasheadas (bcrypt)
- ✅ Validación de fortaleza de contraseñas
- ✅ Tokens JWT con expiración configurable
- ✅ Protección contra CSRF
- ✅ Validación de datos en backend

### 🔧 **Desarrollo**
- ✅ Tests automatizados completos
- ✅ Entorno virtual aislado
- ✅ Migraciones de base de datos
- ✅ API documentada automáticamente
- ✅ Configuración por entorno

## 🏗️ Arquitectura
├── 📁 authentication/ # Sistema de autenticación JWT
├── 📁 presupuestos/ # Gestión de presupuestos
├── 📁 coldrooms/ # Gestión de cuartos fríos
├── 📁 equipos/ # Gestión de equipos
├── 📁 core_project/ # Configuración principal
├── 📄 requirements.txt # Dependencias del proyecto
├── 📄 manage.py # Script de gestión Django
└── 📄 .env.example # Variables de entorno


## 🚀 Instalación

### Prerrequisitos
- Python 3.11 o superior
- PostgreSQL 14+ (recomendado) o SQLite
- Git

### 1. Clonar el repositorio
```bash
git clone https://github.com/tuusuario/backend-suite-budget.git
cd backend-suite-budget

### 2. Configurar entorno virtual
# Crear entorno virtual
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

### 3. Instalar dependencias
pip install -r requirements.txt

### 4. Configurar variables de entorno
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus configuraciones
nano .env  # o usar tu editor preferido

# Variables de entorno requeridas
# Django
SECRET_KEY=tu_clave_secreta_unica
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos
DB_ENGINE=django.db.backends.postgresql
DB_NAME=suite_budget
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

# JWT (opcional, usar valores por defecto o personalizar)
JWT_ACCESS_TOKEN_LIFETIME=5
JWT_REFRESH_TOKEN_LIFETIME=1

### 5. Configurar base de datos
# Aplicar migraciones
python manage.py migrate

# Crear superusuario (opcional)
python manage.py createsuperuser

### 6. Ejecutar servidor de desarrollo
python manage.py runserver





