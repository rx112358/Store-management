import json
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from main.firebase_config import firestore_db
from main.models import Order, OrderItem, Users, Restaurant, Products
from google.cloud.firestore import DocumentSnapshot
import threading
import time

logger = logging.getLogger(__name__)

class RealTimeOrderService:
    """
    Service for managing real-time orders with Firebase Firestore
    """
    
    def __init__(self):
        self.db = firestore_db
        self.listeners = {}  # Store active listeners
        
    def create_order_document(self, order):
        """
        Create an order document in Firestore for real-time tracking
        """
        try:
            order_data = {
                'order_id': str(order.id),
                'user_id': order.user.firebase_uid,
                'user_email': order.user.email,
                'restaurant_id': str(order.restaurant.id),
                'restaurant_name': order.restaurant.name,
                'status': order.status,
                'payment_status': order.payment_status,
                'total_amount': float(order.total_amount),
                'delivery_address': order.delivery_address,
                'delivery_notes': order.delivery_notes,
                'estimated_delivery_time': order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'items': [],
                'timeline': [{
                    'status': 'pending',
                    'timestamp': order.created_at.isoformat(),
                    'message': 'Order placed successfully'
                }]
            }
            
            # Add order items
            for item in order.items.all():
                order_data['items'].append({
                    'product_id': str(item.product.id),
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'unit_price': float(item.unit_price),
                    'total_price': float(item.total_price),
                    'special_instructions': item.special_instructions,
                    'customizations': item.customizations
                })
            
            # Create document in Firestore
            doc_ref = self.db.collection('orders').document()
            doc_ref.set(order_data)
            
            # Update Django model with Firestore document ID
            order.firestore_doc_id = doc_ref.id
            order.save()
            
            logger.info(f"Created Firestore document for order {order.id}")
            return doc_ref.id
            
        except Exception as e:
            logger.error(f"Failed to create Firestore document for order {order.id}: {str(e)}")
            return None
    
    def update_order_status(self, order_id, new_status, message=None):
        """
        Update order status in both Django and Firestore
        """
        try:
            # Update Django model
            order = Order.objects.get(id=order_id)
            old_status = order.status
            order.status = new_status
            order.updated_at = timezone.now()
            order.save()
            
            # Update Firestore document
            if order.firestore_doc_id:
                doc_ref = self.db.collection('orders').document(order.firestore_doc_id)
                
                # Prepare update data
                update_data = {
                    'status': new_status,
                    'updated_at': order.updated_at.isoformat()
                }
                
                # Add timeline entry
                timeline_entry = {
                    'status': new_status,
                    'timestamp': order.updated_at.isoformat(),
                    'message': message or f'Order status changed to {new_status}'
                }
                
                # Use array union to add timeline entry
                from google.cloud.firestore import ArrayUnion
                update_data['timeline'] = ArrayUnion([timeline_entry])
                
                # Set estimated delivery time for certain statuses
                if new_status == 'confirmed':
                    estimated_time = timezone.now() + timedelta(minutes=30)
                    order.estimated_delivery_time = estimated_time
                    order.save()
                    update_data['estimated_delivery_time'] = estimated_time.isoformat()
                elif new_status == 'delivered':
                    order.actual_delivery_time = timezone.now()
                    order.save()
                    update_data['actual_delivery_time'] = order.actual_delivery_time.isoformat()
                
                doc_ref.update(update_data)
                logger.info(f"Updated order {order_id} status from {old_status} to {new_status}")
                
            return True
            
        except Order.DoesNotExist:
            logger.error(f"Order {order_id} not found")
            return False
        except Exception as e:
            logger.error(f"Failed to update order {order_id} status: {str(e)}")
            return False
    
    def get_user_orders(self, firebase_uid, limit=10):
        """
        Get user's orders from Firestore with real-time capability
        """
        try:
            orders_ref = self.db.collection('orders')
            query = orders_ref.where('user_id', '==', firebase_uid).order_by('created_at', direction='DESCENDING').limit(limit)
            
            docs = query.stream()
            orders = []
            
            for doc in docs:
                order_data = doc.to_dict()
                order_data['firestore_id'] = doc.id
                orders.append(order_data)
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get orders for user {firebase_uid}: {str(e)}")
            return []
    
    def get_restaurant_orders(self, restaurant_id, status_filter=None):
        """
        Get restaurant's orders from Firestore
        """
        try:
            orders_ref = self.db.collection('orders')
            query = orders_ref.where('restaurant_id', '==', str(restaurant_id))
            
            if status_filter:
                query = query.where('status', '==', status_filter)
            
            query = query.order_by('created_at', direction='DESCENDING')
            
            docs = query.stream()
            orders = []
            
            for doc in docs:
                order_data = doc.to_dict()
                order_data['firestore_id'] = doc.id
                orders.append(order_data)
            
            return orders
            
        except Exception as e:
            logger.error(f"Failed to get orders for restaurant {restaurant_id}: {str(e)}")
            return []
    
    def listen_to_user_orders(self, firebase_uid, callback):
        """
        Set up real-time listener for user's orders
        """
        try:
            orders_ref = self.db.collection('orders')
            query = orders_ref.where('user_id', '==', firebase_uid)
            
            # Define callback wrapper
            def on_snapshot(docs, changes, read_time):
                try:
                    for change in changes:
                        if change.type.name == 'ADDED':
                            callback('added', change.document.to_dict())
                        elif change.type.name == 'MODIFIED':
                            callback('modified', change.document.to_dict())
                        elif change.type.name == 'REMOVED':
                            callback('removed', change.document.to_dict())
                except Exception as e:
                    logger.error(f"Error in order listener callback: {str(e)}")
            
            # Start listening
            listener = query.on_snapshot(on_snapshot)
            self.listeners[firebase_uid] = listener
            
            logger.info(f"Started listening to orders for user {firebase_uid}")
            return listener
            
        except Exception as e:
            logger.error(f"Failed to set up order listener for user {firebase_uid}: {str(e)}")
            return None
    
    def listen_to_restaurant_orders(self, restaurant_id, callback):
        """
        Set up real-time listener for restaurant's orders
        """
        try:
            orders_ref = self.db.collection('orders')
            query = orders_ref.where('restaurant_id', '==', str(restaurant_id))
            
            def on_snapshot(docs, changes, read_time):
                try:
                    for change in changes:
                        if change.type.name == 'ADDED':
                            callback('added', change.document.to_dict())
                        elif change.type.name == 'MODIFIED':
                            callback('modified', change.document.to_dict())
                        elif change.type.name == 'REMOVED':
                            callback('removed', change.document.to_dict())
                except Exception as e:
                    logger.error(f"Error in restaurant order listener callback: {str(e)}")
            
            listener = query.on_snapshot(on_snapshot)
            self.listeners[f"restaurant_{restaurant_id}"] = listener
            
            logger.info(f"Started listening to orders for restaurant {restaurant_id}")
            return listener
            
        except Exception as e:
            logger.error(f"Failed to set up order listener for restaurant {restaurant_id}: {str(e)}")
            return None
    
    def stop_listener(self, key):
        """
        Stop a real-time listener
        """
        try:
            if key in self.listeners:
                self.listeners[key].unsubscribe()
                del self.listeners[key]
                logger.info(f"Stopped listener for {key}")
                return True
        except Exception as e:
            logger.error(f"Failed to stop listener for {key}: {str(e)}")
        return False
    
    def stop_all_listeners(self):
        """
        Stop all active listeners
        """
        for key in list(self.listeners.keys()):
            self.stop_listener(key)
    
    def delete_order_document(self, order_id):
        """
        Delete order document from Firestore (for cancelled orders)
        """
        try:
            order = Order.objects.get(id=order_id)
            if order.firestore_doc_id:
                self.db.collection('orders').document(order.firestore_doc_id).delete()
                order.firestore_doc_id = ''
                order.save()
                logger.info(f"Deleted Firestore document for order {order_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to delete Firestore document for order {order_id}: {str(e)}")
        return False

# Global instance
realtime_order_service = RealTimeOrderService()