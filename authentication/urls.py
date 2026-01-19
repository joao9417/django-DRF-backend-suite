from django.urls import path
from .views import LogoutView, RegisterUserView, CustomTokenObtainPairView, UserProfileView
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView,)

urlpatterns = [
    #endpoint para registrar usuarios
    path('register/', RegisterUserView.as_view(), name='user_register'),

    #endpoint para login (autenticacion y obtencion de token)
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),

    #endpoint para refresco de token (refrescar token de acceso para no volver a logear)
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    #endpoint para ver el perfil
    path('profile/', UserProfileView.as_view(), name='user_profile'),

    #endpoint para logout
    path('logout/', LogoutView.as_view(), name='user_logout'),

]
