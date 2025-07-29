import json
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from firebase_admin import auth
from main.firebase_config import auth_client
import logging

logger = logging.getLogger(__name__)

class FirebaseAuthenticationMiddleware(MiddlewareMixin):
    """
    Firebase Authentication Middleware
    Verifies Firebase ID tokens and sets user information in request
    """
    
    # Routes that don't require authentication
    EXEMPT_URLS = [
        '/admin/',
        '/signup',
        '/login',
        '/auth/register',
        '/auth/login',
        '/auth/refresh',
        '/static/',
        '/media/',
        '/',
        '/viewProducts'  # Allow public viewing of products
    ]
    
    def process_request(self, request):
        # Skip authentication for exempt URLs
        if any(request.path.startswith(url) for url in self.EXEMPT_URLS):
            return None
        
        # Skip authentication for OPTIONS requests (CORS preflight)
        if request.method == 'OPTIONS':
            return None
        
        # Get Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        
        if not auth_header:
            return JsonResponse({
                'error': 'Authorization header missing',
                'code': 'AUTH_HEADER_MISSING'
            }, status=401)
        
        try:
            # Extract token from "Bearer <token>" format
            if not auth_header.startswith('Bearer '):
                return JsonResponse({
                    'error': 'Invalid authorization header format',
                    'code': 'INVALID_AUTH_FORMAT'
                }, status=401)
            
            id_token = auth_header.split('Bearer ')[1]
            
            # Verify the Firebase ID token
            decoded_token = auth_client.verify_id_token(id_token)
            
            # Add user information to request
            request.firebase_user = {
                'uid': decoded_token['uid'],
                'email': decoded_token.get('email', ''),
                'email_verified': decoded_token.get('email_verified', False),
                'name': decoded_token.get('name', ''),
                'picture': decoded_token.get('picture', ''),
                'firebase_claims': decoded_token
            }
            
        except auth.InvalidIdTokenError:
            return JsonResponse({
                'error': 'Invalid ID token',
                'code': 'INVALID_TOKEN'
            }, status=401)
        except auth.ExpiredIdTokenError:
            return JsonResponse({
                'error': 'Token expired',
                'code': 'TOKEN_EXPIRED'
            }, status=401)
        except Exception as e:
            logger.error(f"Firebase auth error: {str(e)}")
            return JsonResponse({
                'error': 'Authentication failed',
                'code': 'AUTH_FAILED'
            }, status=401)
        
        return None

def firebase_auth_required(view_func):
    """
    Decorator to require Firebase authentication for specific views
    """
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'firebase_user'):
            return JsonResponse({
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper

def firebase_admin_required(view_func):
    """
    Decorator to require Firebase admin authentication for specific views
    """
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'firebase_user'):
            return JsonResponse({
                'error': 'Authentication required',
                'code': 'AUTH_REQUIRED'
            }, status=401)
        
        # Check if user has admin claim
        firebase_claims = request.firebase_user.get('firebase_claims', {})
        if not firebase_claims.get('admin', False):
            return JsonResponse({
                'error': 'Admin access required',
                'code': 'ADMIN_REQUIRED'
            }, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper