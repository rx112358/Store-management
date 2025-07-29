import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from firebase_admin import auth
from main.firebase_config import firebase_client, auth_client
from main.models import Users
from main.middleware.firebase_auth import firebase_auth_required

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(View):
    """
    User registration with Firebase Authentication
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            first_name = data.get('first_name', '')
            last_name = data.get('last_name', '')
            phone_number = data.get('phone_number', '')
            
            if not email or not password:
                return JsonResponse({
                    'error': 'Email and password are required',
                    'code': 'MISSING_CREDENTIALS'
                }, status=400)
            
            # Create user in Firebase Auth
            firebase_auth = firebase_client.auth()
            user = firebase_auth.create_user_with_email_and_password(email, password)
            
            # Send email verification
            firebase_auth.send_email_verification(user['idToken'])
            
            # Create user profile in Django database
            django_user = Users.objects.create(
                firebase_uid=user['localId'],
                email=email,
                first_name=first_name,
                last_name=last_name,
                phone_number=phone_number,
                email_verified=False
            )
            
            return JsonResponse({
                'message': 'User registered successfully',
                'user': {
                    'uid': user['localId'],
                    'email': email,
                    'email_verified': False,
                    'first_name': first_name,
                    'last_name': last_name
                },
                'token': user['idToken']
            }, status=201)
            
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            
            # Handle Firebase-specific errors
            error_message = str(e)
            if 'EMAIL_EXISTS' in error_message:
                return JsonResponse({
                    'error': 'Email already exists',
                    'code': 'EMAIL_EXISTS'
                }, status=400)
            elif 'WEAK_PASSWORD' in error_message:
                return JsonResponse({
                    'error': 'Password is too weak',
                    'code': 'WEAK_PASSWORD'
                }, status=400)
            elif 'INVALID_EMAIL' in error_message:
                return JsonResponse({
                    'error': 'Invalid email format',
                    'code': 'INVALID_EMAIL'
                }, status=400)
            
            return JsonResponse({
                'error': 'Registration failed',
                'code': 'REGISTRATION_FAILED'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(View):
    """
    User login with Firebase Authentication
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')
            
            if not email or not password:
                return JsonResponse({
                    'error': 'Email and password are required',
                    'code': 'MISSING_CREDENTIALS'
                }, status=400)
            
            # Authenticate with Firebase
            firebase_auth = firebase_client.auth()
            user = firebase_auth.sign_in_with_email_and_password(email, password)
            
            # Get user info from Firebase
            user_info = firebase_auth.get_account_info(user['idToken'])
            firebase_user = user_info['users'][0]
            
            # Update or create user in Django database
            django_user, created = Users.objects.get_or_create(
                firebase_uid=firebase_user['localId'],
                defaults={
                    'email': email,
                    'email_verified': firebase_user.get('emailVerified', False)
                }
            )
            
            if not created:
                # Update email verification status
                django_user.email_verified = firebase_user.get('emailVerified', False)
                django_user.save()
            
            return JsonResponse({
                'message': 'Login successful',
                'user': {
                    'uid': firebase_user['localId'],
                    'email': email,
                    'email_verified': django_user.email_verified,
                    'first_name': django_user.first_name,
                    'last_name': django_user.last_name
                },
                'token': user['idToken'],
                'refresh_token': user['refreshToken']
            }, status=200)
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            
            error_message = str(e)
            if 'INVALID_PASSWORD' in error_message or 'EMAIL_NOT_FOUND' in error_message:
                return JsonResponse({
                    'error': 'Invalid email or password',
                    'code': 'INVALID_CREDENTIALS'
                }, status=401)
            elif 'USER_DISABLED' in error_message:
                return JsonResponse({
                    'error': 'User account has been disabled',
                    'code': 'USER_DISABLED'
                }, status=401)
            
            return JsonResponse({
                'error': 'Login failed',
                'code': 'LOGIN_FAILED'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class RefreshTokenView(View):
    """
    Refresh Firebase ID token
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            refresh_token = data.get('refresh_token')
            
            if not refresh_token:
                return JsonResponse({
                    'error': 'Refresh token is required',
                    'code': 'MISSING_REFRESH_TOKEN'
                }, status=400)
            
            firebase_auth = firebase_client.auth()
            refreshed_user = firebase_auth.refresh(refresh_token)
            
            return JsonResponse({
                'token': refreshed_user['idToken'],
                'refresh_token': refreshed_user['refreshToken']
            }, status=200)
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            return JsonResponse({
                'error': 'Token refresh failed',
                'code': 'REFRESH_FAILED'
            }, status=401)

@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetView(View):
    """
    Send password reset email
    """
    
    def post(self, request):
        try:
            data = json.loads(request.body)
            email = data.get('email')
            
            if not email:
                return JsonResponse({
                    'error': 'Email is required',
                    'code': 'MISSING_EMAIL'
                }, status=400)
            
            firebase_auth = firebase_client.auth()
            firebase_auth.send_password_reset_email(email)
            
            return JsonResponse({
                'message': 'Password reset email sent successfully'
            }, status=200)
            
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return JsonResponse({
                'error': 'Failed to send password reset email',
                'code': 'RESET_FAILED'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class EmailVerificationView(View):
    """
    Send email verification
    """
    
    @firebase_auth_required
    def post(self, request):
        try:
            # Get the current user's token
            auth_header = request.META.get('HTTP_AUTHORIZATION')
            id_token = auth_header.split('Bearer ')[1]
            
            firebase_auth = firebase_client.auth()
            firebase_auth.send_email_verification(id_token)
            
            return JsonResponse({
                'message': 'Email verification sent successfully'
            }, status=200)
            
        except Exception as e:
            logger.error(f"Email verification error: {str(e)}")
            return JsonResponse({
                'error': 'Failed to send email verification',
                'code': 'VERIFICATION_FAILED'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ProfileView(View):
    """
    Get and update user profile
    """
    
    @firebase_auth_required
    def get(self, request):
        try:
            firebase_user = request.firebase_user
            
            # Get user from database
            user = Users.objects.get(firebase_uid=firebase_user['uid'])
            
            return JsonResponse({
                'user': {
                    'uid': user.firebase_uid,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'street_address': user.street_address,
                    'city': user.city,
                    'state': user.state,
                    'zip_code': user.zip_code,
                    'email_verified': user.email_verified,
                    'dietary_preferences': user.dietary_preferences,
                    'created_at': user.created_at.isoformat(),
                    'updated_at': user.updated_at.isoformat()
                }
            }, status=200)
            
        except Users.DoesNotExist:
            return JsonResponse({
                'error': 'User profile not found',
                'code': 'USER_NOT_FOUND'
            }, status=404)
        except Exception as e:
            logger.error(f"Profile get error: {str(e)}")
            return JsonResponse({
                'error': 'Failed to get profile',
                'code': 'PROFILE_GET_FAILED'
            }, status=500)
    
    @firebase_auth_required
    def put(self, request):
        try:
            firebase_user = request.firebase_user
            data = json.loads(request.body)
            
            # Get user from database
            user = Users.objects.get(firebase_uid=firebase_user['uid'])
            
            # Update allowed fields
            allowed_fields = [
                'first_name', 'last_name', 'phone_number',
                'street_address', 'city', 'state', 'zip_code',
                'dietary_preferences'
            ]
            
            for field in allowed_fields:
                if field in data:
                    setattr(user, field, data[field])
            
            user.save()
            
            return JsonResponse({
                'message': 'Profile updated successfully',
                'user': {
                    'uid': user.firebase_uid,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'street_address': user.street_address,
                    'city': user.city,
                    'state': user.state,
                    'zip_code': user.zip_code,
                    'dietary_preferences': user.dietary_preferences
                }
            }, status=200)
            
        except Users.DoesNotExist:
            return JsonResponse({
                'error': 'User profile not found',
                'code': 'USER_NOT_FOUND'
            }, status=404)
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}")
            return JsonResponse({
                'error': 'Failed to update profile',
                'code': 'PROFILE_UPDATE_FAILED'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(View):
    """
    Logout user (client-side token deletion)
    """
    
    def post(self, request):
        # Firebase doesn't have server-side logout
        # Token validation happens on each request
        return JsonResponse({
            'message': 'Logout successful. Please delete the token on client side.'
        }, status=200)