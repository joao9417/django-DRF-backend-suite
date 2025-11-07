from rest_framework import generics
from rest_framework.permissions import AllowAny


class RegisterView(generics.CreateAPIView):

    permission_classes = [AllowAny]

    pass