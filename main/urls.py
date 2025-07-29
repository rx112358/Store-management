"""Firebase Food Ordering Application URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from main import view
from main.views.auth import (
    RegisterView, LoginView, LogoutView, RefreshTokenView,
    PasswordResetView, EmailVerificationView, ProfileView
)
from main.views.api import (
    RestaurantsView, MenuView, CartView, OrdersView, OrderDetailView
)

# Authentication URLs
auth_urlpatterns = [
    path('register', RegisterView.as_view(), name='auth_register'),
    path('login', LoginView.as_view(), name='auth_login'),
    path('logout', LogoutView.as_view(), name='auth_logout'),
    path('refresh', RefreshTokenView.as_view(), name='auth_refresh'),
    path('password-reset', PasswordResetView.as_view(), name='auth_password_reset'),
    path('email-verification', EmailVerificationView.as_view(), name='auth_email_verification'),
    path('profile', ProfileView.as_view(), name='auth_profile'),
]

# API URLs
api_urlpatterns = [
    # Restaurant and menu endpoints
    path('restaurants', RestaurantsView.as_view(), name='api_restaurants'),
    path('restaurants/<uuid:restaurant_id>/menu', MenuView.as_view(), name='api_menu'),
    
    # Cart endpoints
    path('cart', CartView.as_view(), name='api_cart'),
    path('cart/<uuid:item_id>', CartView.as_view(), name='api_cart_item'),
    
    # Order endpoints
    path('orders', OrdersView.as_view(), name='api_orders'),
    path('orders/<uuid:order_id>', OrderDetailView.as_view(), name='api_order_detail'),
]

# Main URL patterns
urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Legacy views (keeping for backward compatibility)
    path('', view.wrongPath, name='home'),
    path('signup', view.signUp_page, name='signup_page'),
    path('viewProducts', view.view_Product, name='view_products'),
    path('admin/db_ops', view.admin_dbps, name='admin_db_ops'),
    
    # Authentication API endpoints
    path('auth/', include(auth_urlpatterns)),
    
    # Main API endpoints
    path('api/', include(api_urlpatterns)),
    
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
