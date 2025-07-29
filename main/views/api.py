import json
import logging
from decimal import Decimal
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.db import transaction
from django.utils import timezone
from main.models import (
    Users, Restaurant, Category, Products, 
    Order, OrderItem, Cart
)
from main.middleware.firebase_auth import firebase_auth_required
from main.services.realtime_orders import realtime_order_service

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class RestaurantsView(View):
    """
    API for managing restaurants
    """
    
    def get(self, request):
        """Get list of active restaurants"""
        try:
            restaurants = Restaurant.objects.filter(is_active=True)
            
            restaurant_list = []
            for restaurant in restaurants:
                restaurant_list.append({
                    'id': str(restaurant.id),
                    'name': restaurant.name,
                    'description': restaurant.description,
                    'address': restaurant.address,
                    'phone': restaurant.phone,
                    'email': restaurant.email,
                    'opening_time': restaurant.opening_time.strftime('%H:%M'),
                    'closing_time': restaurant.closing_time.strftime('%H:%M'),
                    'delivery_fee': float(restaurant.delivery_fee),
                    'minimum_order': float(restaurant.minimum_order),
                    'latitude': float(restaurant.latitude) if restaurant.latitude else None,
                    'longitude': float(restaurant.longitude) if restaurant.longitude else None
                })
            
            return JsonResponse({
                'restaurants': restaurant_list,
                'count': len(restaurant_list)
            }, status=200)
            
        except Exception as e:
            logger.error(f"Failed to get restaurants: {str(e)}")
            return JsonResponse({
                'error': 'Failed to fetch restaurants',
                'code': 'FETCH_FAILED'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class MenuView(View):
    """
    API for restaurant menu
    """
    
    def get(self, request, restaurant_id):
        """Get menu for a specific restaurant"""
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, is_active=True)
            
            # Get categories with products
            categories = Category.objects.filter(
                restaurant=restaurant, 
                is_active=True
            ).prefetch_related('products')
            
            menu_data = {
                'restaurant': {
                    'id': str(restaurant.id),
                    'name': restaurant.name,
                    'description': restaurant.description
                },
                'categories': []
            }
            
            for category in categories:
                products = category.products.filter(is_available=True)
                
                category_data = {
                    'id': str(category.id),
                    'name': category.name,
                    'description': category.description,
                    'products': []
                }
                
                for product in products:
                    category_data['products'].append({
                        'id': str(product.id),
                        'name': product.name,
                        'description': product.description,
                        'price': float(product.price),
                        'image_url': product.image_url,
                        'preparation_time': product.preparation_time,
                        'is_vegetarian': product.is_vegetarian,
                        'is_vegan': product.is_vegan,
                        'is_gluten_free': product.is_gluten_free,
                        'spice_level': product.spice_level,
                        'calories': product.calories,
                        'allergens': product.allergens,
                        'average_rating': product.average_rating,
                        'order_count': product.order_count
                    })
                
                if category_data['products']:  # Only include categories with available products
                    menu_data['categories'].append(category_data)
            
            return JsonResponse(menu_data, status=200)
            
        except Restaurant.DoesNotExist:
            return JsonResponse({
                'error': 'Restaurant not found',
                'code': 'RESTAURANT_NOT_FOUND'
            }, status=404)
        except Exception as e:
            logger.error(f"Failed to get menu for restaurant {restaurant_id}: {str(e)}")
            return JsonResponse({
                'error': 'Failed to fetch menu',
                'code': 'MENU_FETCH_FAILED'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class CartView(View):
    """
    API for shopping cart management
    """
    
    @firebase_auth_required
    def get(self, request):
        """Get user's cart"""
        try:
            user = Users.objects.get(firebase_uid=request.firebase_user['uid'])
            cart_items = Cart.objects.filter(user=user).select_related(
                'product', 'restaurant'
            )
            
            cart_data = {
                'items': [],
                'total_amount': 0,
                'restaurant': None
            }
            
            total_amount = Decimal('0')
            current_restaurant = None
            
            for item in cart_items:
                if current_restaurant is None:
                    current_restaurant = item.restaurant
                    cart_data['restaurant'] = {
                        'id': str(item.restaurant.id),
                        'name': item.restaurant.name,
                        'delivery_fee': float(item.restaurant.delivery_fee),
                        'minimum_order': float(item.restaurant.minimum_order)
                    }
                
                item_total = item.total_price
                total_amount += item_total
                
                cart_data['items'].append({
                    'id': str(item.id),
                    'product': {
                        'id': str(item.product.id),
                        'name': item.product.name,
                        'price': float(item.product.price),
                        'image_url': item.product.image_url
                    },
                    'quantity': item.quantity,
                    'customizations': item.customizations,
                    'special_instructions': item.special_instructions,
                    'total_price': float(item_total)
                })
            
            cart_data['total_amount'] = float(total_amount)
            
            return JsonResponse(cart_data, status=200)
            
        except Users.DoesNotExist:
            return JsonResponse({
                'error': 'User not found',
                'code': 'USER_NOT_FOUND'
            }, status=404)
        except Exception as e:
            logger.error(f"Failed to get cart: {str(e)}")
            return JsonResponse({
                'error': 'Failed to fetch cart',
                'code': 'CART_FETCH_FAILED'
            }, status=500)
    
    @firebase_auth_required
    def post(self, request):
        """Add item to cart"""
        try:
            user = Users.objects.get(firebase_uid=request.firebase_user['uid'])
            data = json.loads(request.body)
            
            product_id = data.get('product_id')
            quantity = data.get('quantity', 1)
            customizations = data.get('customizations', {})
            special_instructions = data.get('special_instructions', '')
            
            if not product_id:
                return JsonResponse({
                    'error': 'Product ID is required',
                    'code': 'MISSING_PRODUCT_ID'
                }, status=400)
            
            product = Products.objects.get(id=product_id, is_available=True)
            
            # Check if user has items from different restaurant
            existing_cart = Cart.objects.filter(user=user).first()
            if existing_cart and existing_cart.restaurant != product.restaurant:
                return JsonResponse({
                    'error': 'Cannot add items from different restaurants',
                    'code': 'DIFFERENT_RESTAURANT',
                    'current_restaurant': existing_cart.restaurant.name,
                    'new_restaurant': product.restaurant.name
                }, status=400)
            
            # Add or update cart item
            cart_item, created = Cart.objects.get_or_create(
                user=user,
                product=product,
                defaults={
                    'restaurant': product.restaurant,
                    'quantity': quantity,
                    'customizations': customizations,
                    'special_instructions': special_instructions
                }
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.customizations.update(customizations)
                if special_instructions:
                    cart_item.special_instructions = special_instructions
                cart_item.save()
            
            return JsonResponse({
                'message': 'Item added to cart successfully',
                'cart_item': {
                    'id': str(cart_item.id),
                    'quantity': cart_item.quantity,
                    'total_price': float(cart_item.total_price)
                }
            }, status=201)
            
        except Products.DoesNotExist:
            return JsonResponse({
                'error': 'Product not found or not available',
                'code': 'PRODUCT_NOT_FOUND'
            }, status=404)
        except Exception as e:
            logger.error(f"Failed to add item to cart: {str(e)}")
            return JsonResponse({
                'error': 'Failed to add item to cart',
                'code': 'CART_ADD_FAILED'
            }, status=500)
    
    @firebase_auth_required
    def put(self, request, item_id):
        """Update cart item quantity"""
        try:
            user = Users.objects.get(firebase_uid=request.firebase_user['uid'])
            data = json.loads(request.body)
            quantity = data.get('quantity')
            
            if quantity is None or quantity < 0:
                return JsonResponse({
                    'error': 'Valid quantity is required',
                    'code': 'INVALID_QUANTITY'
                }, status=400)
            
            cart_item = Cart.objects.get(id=item_id, user=user)
            
            if quantity == 0:
                cart_item.delete()
                return JsonResponse({
                    'message': 'Item removed from cart'
                }, status=200)
            else:
                cart_item.quantity = quantity
                cart_item.save()
                return JsonResponse({
                    'message': 'Cart item updated successfully',
                    'cart_item': {
                        'id': str(cart_item.id),
                        'quantity': cart_item.quantity,
                        'total_price': float(cart_item.total_price)
                    }
                }, status=200)
            
        except Cart.DoesNotExist:
            return JsonResponse({
                'error': 'Cart item not found',
                'code': 'CART_ITEM_NOT_FOUND'
            }, status=404)
        except Exception as e:
            logger.error(f"Failed to update cart item: {str(e)}")
            return JsonResponse({
                'error': 'Failed to update cart item',
                'code': 'CART_UPDATE_FAILED'
            }, status=500)
    
    @firebase_auth_required
    def delete(self, request):
        """Clear cart"""
        try:
            user = Users.objects.get(firebase_uid=request.firebase_user['uid'])
            Cart.objects.filter(user=user).delete()
            
            return JsonResponse({
                'message': 'Cart cleared successfully'
            }, status=200)
            
        except Exception as e:
            logger.error(f"Failed to clear cart: {str(e)}")
            return JsonResponse({
                'error': 'Failed to clear cart',
                'code': 'CART_CLEAR_FAILED'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class OrdersView(View):
    """
    API for order management
    """
    
    @firebase_auth_required
    def get(self, request):
        """Get user's orders"""
        try:
            user = Users.objects.get(firebase_uid=request.firebase_user['uid'])
            orders = Order.objects.filter(user=user).select_related(
                'restaurant'
            ).prefetch_related('items__product')
            
            orders_data = []
            for order in orders:
                order_data = {
                    'id': str(order.id),
                    'restaurant': {
                        'id': str(order.restaurant.id),
                        'name': order.restaurant.name
                    },
                    'status': order.status,
                    'payment_status': order.payment_status,
                    'total_amount': float(order.total_amount),
                    'delivery_address': order.delivery_address,
                    'estimated_delivery_time': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
                    'created_at': order.created_at.isoformat(),
                    'items': []
                }
                
                for item in order.items.all():
                    order_data['items'].append({
                        'product_name': item.product.name,
                        'quantity': item.quantity,
                        'unit_price': float(item.unit_price),
                        'total_price': float(item.total_price),
                        'special_instructions': item.special_instructions
                    })
                
                orders_data.append(order_data)
            
            return JsonResponse({
                'orders': orders_data,
                'count': len(orders_data)
            }, status=200)
            
        except Exception as e:
            logger.error(f"Failed to get orders: {str(e)}")
            return JsonResponse({
                'error': 'Failed to fetch orders',
                'code': 'ORDERS_FETCH_FAILED'
            }, status=500)
    
    @firebase_auth_required
    def post(self, request):
        """Create new order from cart"""
        try:
            user = Users.objects.get(firebase_uid=request.firebase_user['uid'])
            data = json.loads(request.body)
            
            delivery_address = data.get('delivery_address')
            delivery_notes = data.get('delivery_notes', '')
            tip_amount = Decimal(str(data.get('tip_amount', 0)))
            
            if not delivery_address:
                return JsonResponse({
                    'error': 'Delivery address is required',
                    'code': 'MISSING_DELIVERY_ADDRESS'
                }, status=400)
            
            # Get cart items
            cart_items = Cart.objects.filter(user=user).select_related(
                'product', 'restaurant'
            )
            
            if not cart_items:
                return JsonResponse({
                    'error': 'Cart is empty',
                    'code': 'EMPTY_CART'
                }, status=400)
            
            restaurant = cart_items.first().restaurant
            
            # Calculate totals
            subtotal = sum(item.total_price for item in cart_items)
            tax_rate = Decimal('0.08')  # 8% tax
            tax_amount = subtotal * tax_rate
            delivery_fee = restaurant.delivery_fee
            total_amount = subtotal + tax_amount + delivery_fee + tip_amount
            
            # Check minimum order
            if subtotal < restaurant.minimum_order:
                return JsonResponse({
                    'error': f'Minimum order amount is ${restaurant.minimum_order}',
                    'code': 'MINIMUM_ORDER_NOT_MET',
                    'minimum_order': float(restaurant.minimum_order),
                    'current_total': float(subtotal)
                }, status=400)
            
            # Create order in transaction
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    restaurant=restaurant,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    delivery_fee=delivery_fee,
                    tip_amount=tip_amount,
                    total_amount=total_amount,
                    delivery_address=delivery_address,
                    delivery_notes=delivery_notes,
                    status='pending',
                    payment_status='pending'
                )
                
                # Create order items
                for cart_item in cart_items:
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        unit_price=cart_item.product.price,
                        special_instructions=cart_item.special_instructions,
                        customizations=cart_item.customizations
                    )
                    
                    # Update product order count
                    cart_item.product.order_count += cart_item.quantity
                    cart_item.product.save()
                
                # Clear cart
                cart_items.delete()
                
                # Create Firestore document for real-time tracking
                realtime_order_service.create_order_document(order)
            
            return JsonResponse({
                'message': 'Order created successfully',
                'order': {
                    'id': str(order.id),
                    'total_amount': float(order.total_amount),
                    'status': order.status,
                    'estimated_delivery_time': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None
                }
            }, status=201)
            
        except Exception as e:
            logger.error(f"Failed to create order: {str(e)}")
            return JsonResponse({
                'error': 'Failed to create order',
                'code': 'ORDER_CREATE_FAILED'
            }, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class OrderDetailView(View):
    """
    API for individual order details
    """
    
    @firebase_auth_required
    def get(self, request, order_id):
        """Get order details"""
        try:
            user = Users.objects.get(firebase_uid=request.firebase_user['uid'])
            order = Order.objects.get(id=order_id, user=user)
            
            order_data = {
                'id': str(order.id),
                'restaurant': {
                    'id': str(order.restaurant.id),
                    'name': order.restaurant.name,
                    'phone': order.restaurant.phone
                },
                'status': order.status,
                'payment_status': order.payment_status,
                'subtotal': float(order.subtotal),
                'tax_amount': float(order.tax_amount),
                'delivery_fee': float(order.delivery_fee),
                'tip_amount': float(order.tip_amount),
                'total_amount': float(order.total_amount),
                'delivery_address': order.delivery_address,
                'delivery_notes': order.delivery_notes,
                'estimated_delivery_time': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
                'actual_delivery_time': order.actual_delivery_time.isoformat() if order.actual_delivery_time else None,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'items': []
            }
            
            for item in order.items.all():
                order_data['items'].append({
                    'id': str(item.id),
                    'product': {
                        'id': str(item.product.id),
                        'name': item.product.name,
                        'image_url': item.product.image_url
                    },
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price),
                    'special_instructions': item.special_instructions,
                    'customizations': item.customizations
                })
            
            return JsonResponse(order_data, status=200)
            
        except Order.DoesNotExist:
            return JsonResponse({
                'error': 'Order not found',
                'code': 'ORDER_NOT_FOUND'
            }, status=404)
        except Exception as e:
            logger.error(f"Failed to get order details: {str(e)}")
            return JsonResponse({
                'error': 'Failed to fetch order details',
                'code': 'ORDER_DETAIL_FAILED'
            }, status=500)