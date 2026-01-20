from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static

# configuracion de Swagger/OpenAPI
schema_view = get_schema_view(
    openapi.Info(
        title="Suite Budget API",
        default_version='v1',
        description="""
        # API Documentation - suite budget

        sistema de gestion de presupuestos con autenticacion JWT

        ## Autenticacion:
            1. Registro: Crear un nuevo usuario
            2. login: obten tus tokens JWT
            3. Refresh: Renueva tu token de acceso
        
        ## Endpoints disponibles
            **Autenticacion: Registro, Login, Perfil de usuario
            **Presupuestos: Gestion de presupuestos
            **Coldrooms: Gestion de cuartos frios
            **Equipos: Gestion de equipos
        
        ## Uso de tokens
            una vez autenticado, usa el token asi:
            ```
            Authorization: Bearer <tu_token_jwt>
            ```
        
        ## Notas importantes
            -Todos los endpoints (excepto registro y login) requieren autenticacion
            -Los tokens expiran despues de 60 minutos (configurable)
            -Usa el refresh token para obtener nuevos access tokens
        """,
        terms_of_service="https://www.misitio.com/terminos/",
        contact=openapi.Contact(email="soporte@misitio.com"),
        license=openapi.License(name="MIT license"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)



urlpatterns = [
    #ruta administracion de django
    path('admin/', admin.site.urls),

    # Documentación Swagger/OpenAPI
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), 
         name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), 
         name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), 
         name='schema-json'),
    path('swagger.yaml', schema_view.without_ui(cache_timeout=0), 
         name='schema-yaml'),    
    
    #acoplamiento y versionamiento de la API
    path('api/v1/', include('authentication.urls')),
    
    #rutas de la aplicacion presupuestos
    path('api/v1/', include('presupuestos.urls')),
    
    #rutas de la aplicacion coldrooms
    path('api/v1/', include('coldrooms.urls')),

    #rutas de la aplicacion equipos
    path('api/v1/', include('equipos.urls')),
]

# Servir archivos estáticos en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
