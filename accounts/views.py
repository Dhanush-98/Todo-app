from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from .models import User
from .serializers import UserSerializer
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from rest_framework.permissions import AllowAny
from .firebase_auth.firebase_authentication import auth as firebase_admin_auth
from django.contrib.auth.hashers import check_password
import re
from todo.settings import auth


class AuthCreateNewUserView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    @swagger_auto_schema(
        operation_summary="Create a new user",
        operation_description="Create a new user by providing the required fields.",
        tags=["User Management"],
        request_body=UserSerializer,
        responses={201: UserSerializer(many=False), 400: "User creation failed."}
    )
    def post(self, request, format=None):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        included_fields = [email, password, first_name, last_name]
        # Check if any of the required fields are missing
        if not all(included_fields):
            bad_response = {
                "status": "failed",
                "message": "All fields are required.",
            }
            return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)
        # Check if email is valid
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            bad_response = {
                "status": "failed",
                "message": "Enter a valid email address."
            }
            return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)
      # Check if password is less than 8 characters
        if len(password) < 8:
            bad_response = {
                "status": "failed",
                "message": "Password must be at least 8 characters long."
            }
            return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)
        try:
            # create user on firebase
            # TODO: Implement email verification
            display_name = f"{first_name} {last_name}"
            user = firebase_admin_auth.create_user(email=email, password=password, email_verified=True, display_name=display_name)
            # create user on django database
            uid = user.uid
            data["firebase_uid"] = uid
            data["is_active"] = True

            serializer = UserSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                response = {
                    "status": "success",
                    "message": "User created successfully.",
                    "data": serializer.data
                }
                return Response(response, status=status.HTTP_201_CREATED)
            else:
                firebase_admin_auth.delete_user(user.uid)
                bad_response = {
                    "status": "failed",
                    "message": "User signup failed.",
                    "data": serializer.errors
                }
                return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            bad_response = {
                "status": "failed",
                "message": str(e)
            }
            return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)
      

class AuthLoginExisitingUserView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    @swagger_auto_schema(
        operation_summary="Login an existing user",
        operation_description="Login an existing user by providing the required fields.",
        tags=["User Management"],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email of the user'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password of the user')
            }
        ),
        responses={200: UserSerializer(many=False), 404: "User does not exist."}
    )
    def post(self, request: Request):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        try:
            user = auth.sign_in_with_email_and_password(email, password)
        except Exception:
            bad_response = {
                "status": "failed",
                "message": "Invalid email or password."
            }
            return Response(bad_response, status=status.HTTP_400_BAD_REQUEST)
        try:
            existing_user = User.objects.get(email=email)
            serializer = UserSerializer(existing_user)
            extra_data = {
                "firebase_id": user['localId'],
                "firebase_access_token": user['idToken'],
                "firebase_refresh_token": user['refreshToken'],
                "firebase_expires_in": user['expiresIn'],
                "firebase_kind": user['kind'],
                "user_data": serializer.data
            }
            response = {
                "status": "success",
                "message": "User logged in successfully.",
                "data": extra_data
            }
            return Response(response, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            # Delete user from firebase, because user doesn't exist in our database
            auth.delete_user_account(user['idToken'])
            bad_response = {
                "status": "failed",
                "message": "User does not exist."
            }
            return Response(bad_response, status=status.HTTP_404_NOT_FOUND)
