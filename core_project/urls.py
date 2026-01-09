"""
URL configuration for core_project project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    #ruta administracion de django
    path('admin/', admin.site.urls),
    
    #acoplamiento y versionamiento de la API
    path('api/v1/', include('authentication.urls')),
    
    #rutas de la aplicacion presupuestos
    path('api/v1/presupuestos/', include('presupuestos.urls')),
    
    #rutas de la aplicacion coldrooms
    path('api/v1/coldrooms/', include('coldrooms.urls')),

    #rutas de la aplicacion equipos
    path('api/v1/equipos/', include('equipos.urls')),
]
