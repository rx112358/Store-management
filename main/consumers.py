import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from firebase_admin import auth
from main.models import Users, Order, Restaurant
from main.services.realtime_orders import realtime_order_service

logger = logging.getLogger(__name__)

class OrderTrackingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time order tracking
    """
    
    async def connect(self):
        """
        Handle WebSocket connection
        """
        try:
            # Get token from query parameters
            token = self.scope['query_string'].decode().split('token=')[1] if 'token=' in self.scope['query_string'].decode() else None
            
            if not token:
                await self.close(code=4001)  # Unauthorized
                return
            
            # Verify Firebase token
            try:
                decoded_token = auth.verify_id_token(token)
                self.firebase_uid = decoded_token['uid']
            except Exception as e:
                logger.error(f"Invalid token in WebSocket: {str(e)}")
                await self.close(code=4001)  # Unauthorized
                return
            
            # Add user to their personal group
            self.user_group_name = f"user_{self.firebase_uid}"
            await self.channel_layer.group_add(
                self.user_group_name,
                self.channel_name
            )
            
            await self.accept()
            logger.info(f"WebSocket connected for user {self.firebase_uid}")
            
        except Exception as e:
            logger.error(f"WebSocket connection error: {str(e)}")
            await self.close(code=4000)  # Bad request
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
            logger.info(f"WebSocket disconnected for user {self.firebase_uid}")
    
    async def receive(self, text_data):
        """
        Handle messages from WebSocket
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'subscribe_orders':
                # Send current orders to the user
                await self.send_user_orders()
            elif message_type == 'ping':
                # Respond to ping with pong
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': data.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"WebSocket receive error: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def send_user_orders(self):
        """
        Send user's current orders
        """
        try:
            orders = await self.get_user_orders()
            await self.send(text_data=json.dumps({
                'type': 'orders_list',
                'orders': orders
            }))
        except Exception as e:
            logger.error(f"Error sending user orders: {str(e)}")
    
    @database_sync_to_async
    def get_user_orders(self):
        """
        Get user's orders from database
        """
        try:
            user = Users.objects.get(firebase_uid=self.firebase_uid)
            orders = Order.objects.filter(user=user).select_related('restaurant')[:10]
            
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': str(order.id),
                    'restaurant_name': order.restaurant.name,
                    'status': order.status,
                    'total_amount': float(order.total_amount),
                    'estimated_delivery_time': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
                    'created_at': order.created_at.isoformat()
                })
            
            return orders_data
        except Exception as e:
            logger.error(f"Error getting user orders: {str(e)}")
            return []
    
    # Event handlers for group messages
    async def order_status_update(self, event):
        """
        Handle order status update messages
        """
        await self.send(text_data=json.dumps({
            'type': 'order_update',
            'order_id': event['order_id'],
            'status': event['status'],
            'message': event.get('message', ''),
            'timestamp': event['timestamp']
        }))
    
    async def order_created(self, event):
        """
        Handle new order creation messages
        """
        await self.send(text_data=json.dumps({
            'type': 'order_created',
            'order': event['order'],
            'timestamp': event['timestamp']
        }))

class RestaurantOrderConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for restaurant order management
    """
    
    async def connect(self):
        """
        Handle WebSocket connection for restaurant
        """
        try:
            self.restaurant_id = self.scope['url_route']['kwargs']['restaurant_id']
            
            # Get token from query parameters
            token = self.scope['query_string'].decode().split('token=')[1] if 'token=' in self.scope['query_string'].decode() else None
            
            if not token:
                await self.close(code=4001)  # Unauthorized
                return
            
            # Verify Firebase token and check restaurant access
            try:
                decoded_token = auth.verify_id_token(token)
                self.firebase_uid = decoded_token['uid']
                
                # Check if user has restaurant access (admin or restaurant owner)
                has_access = await self.check_restaurant_access()
                if not has_access:
                    await self.close(code=4003)  # Forbidden
                    return
                    
            except Exception as e:
                logger.error(f"Invalid token in restaurant WebSocket: {str(e)}")
                await self.close(code=4001)  # Unauthorized
                return
            
            # Add to restaurant group
            self.restaurant_group_name = f"restaurant_{self.restaurant_id}"
            await self.channel_layer.group_add(
                self.restaurant_group_name,
                self.channel_name
            )
            
            await self.accept()
            logger.info(f"Restaurant WebSocket connected for restaurant {self.restaurant_id}")
            
        except Exception as e:
            logger.error(f"Restaurant WebSocket connection error: {str(e)}")
            await self.close(code=4000)  # Bad request
    
    async def disconnect(self, close_code):
        """
        Handle WebSocket disconnection
        """
        if hasattr(self, 'restaurant_group_name'):
            await self.channel_layer.group_discard(
                self.restaurant_group_name,
                self.channel_name
            )
            logger.info(f"Restaurant WebSocket disconnected for restaurant {self.restaurant_id}")
    
    async def receive(self, text_data):
        """
        Handle messages from restaurant WebSocket
        """
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'update_order_status':
                order_id = data.get('order_id')
                new_status = data.get('status')
                message = data.get('message', '')
                
                if order_id and new_status:
                    await self.update_order_status(order_id, new_status, message)
            elif message_type == 'get_orders':
                await self.send_restaurant_orders()
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))
        except Exception as e:
            logger.error(f"Restaurant WebSocket receive error: {str(e)}")
    
    @database_sync_to_async
    def check_restaurant_access(self):
        """
        Check if user has access to restaurant orders
        """
        # For now, allow all authenticated users
        # In production, implement proper role-based access control
        return True
    
    @database_sync_to_async
    def update_order_status(self, order_id, new_status, message):
        """
        Update order status and notify relevant users
        """
        try:
            # Update order status using the realtime service
            success = realtime_order_service.update_order_status(order_id, new_status, message)
            
            if success:
                # Get order details to send to user
                order = Order.objects.get(id=order_id)
                
                # Send update to user
                from channels.layers import get_channel_layer
                channel_layer = get_channel_layer()
                
                # Send to user's personal channel
                user_group_name = f"user_{order.user.firebase_uid}"
                channel_layer.group_send(
                    user_group_name,
                    {
                        'type': 'order_status_update',
                        'order_id': str(order_id),
                        'status': new_status,
                        'message': message,
                        'timestamp': order.updated_at.isoformat()
                    }
                )
                
                return True
        except Exception as e:
            logger.error(f"Error updating order status: {str(e)}")
            return False
    
    async def send_restaurant_orders(self):
        """
        Send restaurant's current orders
        """
        try:
            orders = await self.get_restaurant_orders()
            await self.send(text_data=json.dumps({
                'type': 'restaurant_orders',
                'orders': orders
            }))
        except Exception as e:
            logger.error(f"Error sending restaurant orders: {str(e)}")
    
    @database_sync_to_async
    def get_restaurant_orders(self):
        """
        Get restaurant's orders from database
        """
        try:
            orders = Order.objects.filter(
                restaurant_id=self.restaurant_id
            ).exclude(status='delivered').select_related('user')[:20]
            
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': str(order.id),
                    'user_email': order.user.email,
                    'status': order.status,
                    'total_amount': float(order.total_amount),
                    'delivery_address': order.delivery_address,
                    'estimated_delivery_time': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
                    'created_at': order.created_at.isoformat()
                })
            
            return orders_data
        except Exception as e:
            logger.error(f"Error getting restaurant orders: {str(e)}")
            return []
    
    # Event handlers for group messages
    async def new_order(self, event):
        """
        Handle new order notifications for restaurant
        """
        await self.send(text_data=json.dumps({
            'type': 'new_order',
            'order': event['order'],
            'timestamp': event['timestamp']
        }))