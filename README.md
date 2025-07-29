# Firebase Food Ordering System

A real-time food ordering web application built with Django, Firebase Authentication, and WebSocket connections for live order tracking.

## 🚀 Features

### Authentication & User Management
- **Firebase Authentication** integration with email/password signup and login
- **JWT token-based** API authentication
- **Email verification** and password reset functionality
- **User profile management** with delivery address storage

### Real-time Order Management
- **Live order tracking** using Firebase Firestore and WebSockets
- **Real-time status updates** for customers and restaurants
- **Order timeline** with detailed status progression
- **Push notifications** for order status changes

### Food Ordering System
- **Multi-restaurant support** with individual menus
- **Category-based menu organization** with product filtering
- **Shopping cart** with customization options
- **Order calculation** with taxes, delivery fees, and tips
- **Order history** and detailed receipts

### Technical Features
- **Django REST API** with comprehensive endpoints
- **WebSocket consumers** for real-time communication
- **Redis caching** and session management
- **Responsive UI** with Tailwind CSS
- **Modern JavaScript** with async/await patterns

## 🛠️ Technology Stack

### Backend
- **Django 4.2** - Web framework
- **Django REST Framework** - API development
- **Django Channels** - WebSocket support
- **Firebase Admin SDK** - Authentication and Firestore
- **Redis** - Caching and WebSocket messaging
- **SQLite/PostgreSQL** - Database

### Frontend
- **HTML5/CSS3** - Structure and styling
- **Tailwind CSS** - Utility-first CSS framework
- **Vanilla JavaScript** - Client-side logic
- **Firebase Web SDK** - Authentication
- **WebSocket API** - Real-time communication

### Firebase Services
- **Firebase Authentication** - User management
- **Cloud Firestore** - Real-time database
- **Firebase Admin SDK** - Server-side operations

## 📋 Prerequisites

Before running this application, make sure you have:

1. **Python 3.8+** installed
2. **Node.js** (for frontend dependencies, optional)
3. **Redis server** running
4. **Firebase project** set up with:
   - Authentication enabled (Email/Password)
   - Cloud Firestore database
   - Service account key generated

## 🔧 Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd firebase-food-ordering
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Firebase Configuration

#### Create Firebase Project
1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Create a new project
3. Enable Authentication with Email/Password
4. Create a Firestore database
5. Generate a service account key

#### Download Service Account Key
1. Go to Project Settings → Service Accounts
2. Generate new private key
3. Save as `firebase-service-account.json` in project root

#### Get Firebase Config
1. Go to Project Settings → General
2. Add a web app to get the config object

### 4. Environment Variables

Create a `.env` file in the project root:

```bash
# Copy from example
cp .env.example .env
```

Update the `.env` file with your Firebase configuration:

```env
# Firebase Configuration
FIREBASE_API_KEY=your-firebase-api-key
FIREBASE_AUTH_DOMAIN=your-project.firebaseapp.com
FIREBASE_DATABASE_URL=https://your-project-default-rtdb.firebaseio.com/
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_STORAGE_BUCKET=your-project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your-messaging-sender-id
FIREBASE_APP_ID=your-app-id

# Firebase Admin SDK Service Account
FIREBASE_PRIVATE_KEY_ID=your-private-key-id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nyour-private-key\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-xxxxx@your-project.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=your-client-id
FIREBASE_CLIENT_CERT_URL=https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-xxxxx%40your-project.iam.gserviceaccount.com

# Django Configuration
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

### 5. Update Firebase Config in Frontend

Edit `templates/firebase_auth.html` and update the Firebase configuration:

```javascript
const firebaseConfig = {
    apiKey: "your-api-key",
    authDomain: "your-project.firebaseapp.com",
    projectId: "your-project-id",
    storageBucket: "your-project.appspot.com",
    messagingSenderId: "your-sender-id",
    appId: "your-app-id"
};
```

### 6. Database Setup

```bash
# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

### 7. Start Redis Server

Make sure Redis is running on your system:

```bash
# On macOS with Homebrew:
brew services start redis

# On Ubuntu:
sudo systemctl start redis-server

# On Windows, download and run Redis from official website
```

## 🚀 Running the Application

### 1. Start Django Development Server

```bash
python manage.py runserver
```

### 2. Access the Application

- **Main Application**: http://localhost:8000/
- **Modern UI**: http://localhost:8000/templates/firebase_auth.html
- **Admin Panel**: http://localhost:8000/admin/
- **API Documentation**: http://localhost:8000/api/

## 📱 API Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/logout` - User logout
- `POST /auth/refresh` - Refresh token
- `POST /auth/password-reset` - Password reset
- `GET/PUT /auth/profile` - User profile management

### Restaurants & Menu
- `GET /api/restaurants` - List all restaurants
- `GET /api/restaurants/{id}/menu` - Get restaurant menu

### Shopping Cart
- `GET /api/cart` - Get user's cart
- `POST /api/cart` - Add item to cart
- `PUT /api/cart/{item_id}` - Update cart item
- `DELETE /api/cart` - Clear cart

### Orders
- `GET /api/orders` - Get user's orders
- `POST /api/orders` - Create new order
- `GET /api/orders/{id}` - Get order details

### WebSocket Endpoints
- `ws://localhost:8000/ws/orders/` - User order tracking
- `ws://localhost:8000/ws/restaurant/{id}/orders/` - Restaurant order management

## 🧪 Testing the Application

### 1. Create Sample Data

```bash
python manage.py shell
```

```python
from main.models import Restaurant, Category, Products
from datetime import time

# Create a restaurant
restaurant = Restaurant.objects.create(
    name="Pizza Palace",
    description="Authentic Italian pizzas",
    address="123 Main St, City",
    phone="555-0123",
    email="info@pizzapalace.com",
    opening_time=time(9, 0),
    closing_time=time(22, 0),
    delivery_fee=3.99,
    minimum_order=15.00
)

# Create categories
appetizers = Category.objects.create(
    restaurant=restaurant,
    name="Appetizers",
    description="Start your meal right"
)

pizzas = Category.objects.create(
    restaurant=restaurant,
    name="Pizzas",
    description="Hand-tossed authentic pizzas"
)

# Create products
Products.objects.create(
    restaurant=restaurant,
    category=appetizers,
    name="Garlic Bread",
    description="Fresh baked with herbs",
    price=6.99,
    is_available=True
)

Products.objects.create(
    restaurant=restaurant,
    category=pizzas,
    name="Margherita Pizza",
    description="Fresh tomatoes, mozzarella, basil",
    price=16.99,
    is_available=True,
    is_vegetarian=True
)
```

### 2. Test Authentication Flow

1. Open http://localhost:8000/templates/firebase_auth.html
2. Click "Sign Up" and create a new account
3. Verify the user appears in Firebase Console
4. Test login functionality
5. Check that JWT tokens are working with API calls

### 3. Test Real-time Features

1. Register and login with a user account
2. Add items to cart and place an order
3. Open browser developer tools and check WebSocket connection
4. Use Django admin or API to update order status
5. Verify real-time notifications appear in the frontend

## 🔒 Security Considerations

### Production Deployment

1. **Environment Variables**: Never commit `.env` file or service account keys
2. **HTTPS**: Always use HTTPS in production
3. **Firebase Rules**: Set up proper Firestore security rules
4. **Rate Limiting**: Implement API rate limiting
5. **CORS**: Configure CORS for production domains

### Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Orders are only accessible to the order owner
    match /orders/{orderId} {
      allow read, write: if request.auth != null && 
        request.auth.uid == resource.data.user_id;
    }
  }
}
```

## 🐛 Troubleshooting

### Common Issues

1. **Redis Connection Error**
   ```bash
   # Check if Redis is running
   redis-cli ping
   # Should return "PONG"
   ```

2. **Firebase Authentication Issues**
   - Verify Firebase project configuration
   - Check that Authentication is enabled
   - Ensure service account key is valid

3. **WebSocket Connection Issues**
   - Verify Redis is running
   - Check Django Channels configuration
   - Ensure proper token authentication

4. **Database Migration Issues**
   ```bash
   # Reset migrations if needed
   python manage.py migrate --fake-initial
   ```

### Logs and Debugging

Check application logs in the `logs/` directory:
- `django.log` - General application logs
- Check browser console for frontend errors
- Use Django debug toolbar for API debugging

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

For support and questions:
- Create an issue in the repository
- Check the troubleshooting section
- Review Firebase and Django documentation

## 🔮 Future Enhancements

- Payment integration (Stripe/PayPal)
- Push notifications (FCM)
- Location-based restaurant discovery
- Review and rating system
- Driver tracking for deliveries
- Multi-language support
- Mobile app development