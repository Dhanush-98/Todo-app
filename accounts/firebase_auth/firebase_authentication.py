from rest_framework import authentication
from .firebase_exceptions import NoAuthToken, InvalidAuthToken, FirebaseError, EmailVerification
from firebase_admin import auth, credentials
import firebase_admin
from accounts.models import User
from django.db import IntegrityError
import os
# Firebase Admin SDK credentials
try:
    cred = credentials.Certificate(os.getenv('FIREBASE_ADMIN_SDK_CREDENTIALS_PATH'))
    default_app = firebase_admin.initialize_app(cred)
except Exception:
    raise FirebaseError("Firebase Admin SDK credentials not found. Please add the path to the credentials file to the FIREBASE_ADMIN_SDK_CREDENTIALS_PATH environment variable.")

class FirebaseAuthentication(authentication.BaseAuthentication):
    keyword = 'Bearer'
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            raise NoAuthToken("No authentication token provided.")
        id_token = auth_header.split(' ').pop()
        decoded_token = None
        try:
          decoded_token = auth.verify_id_token(id_token)
        except Exception:
            raise InvalidAuthToken("Invalid authentication token provided.")
        if not id_token or not decoded_token:
            return None
        email_verified = decoded_token.get('email_verified')
        if not email_verified:
            raise EmailVerification("Email not verified. please verify your email address.")
        try:
            uid = decoded_token.get('uid')
        except Exception:
            raise FirebaseError("The user proivded with auth token is not a firebase user. it has no firebase uid.")
        try:
            user, _= User.objects.get_or_create(
                firebase_uid=uid,
                defaults={
                    "first_name": decoded_token.get("display_name"),
                    "phone_number": decoded_token.get("phone_number")
                }
            )
        except IntegrityError as e:
            raise FirebaseError(f"Error creating or accessing user data: {e}")
        except Exception as e:
            raise FirebaseError(f"Error accessing user data: {e}")
        return (user, None)
