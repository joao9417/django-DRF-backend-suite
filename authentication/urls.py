from django.urls import path
from .views import RegisterUserView

urlpatterns = [
    #endpoint para registrar usuarios
    path('register/', RegisterUserView.as_view(), name='user_register'),
]
