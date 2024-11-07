from django.urls import path
from accounts.views import (
AuthCreateNewUserView,
AuthLoginExisitingUserView,
)
urlpatterns = [
    path('auth/sign-up/', AuthCreateNewUserView.as_view(), name='auth-create-user'),
    path('auth/sign-in/', AuthLoginExisitingUserView.as_view(), name='auth-login-user'),
]
