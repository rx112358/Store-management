from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import time
from main.models import Restaurant, Category, Products
import uuid

class Command(BaseCommand):
    help = 'Create sample data for testing the food ordering application'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before creating sample data',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing data...')
            Products.objects.all().delete()
            Category.objects.all().delete()
            Restaurant.objects.all().delete()

        self.stdout.write('Creating sample restaurants...')
        
        # Create Pizza Palace
        pizza_palace = Restaurant.objects.create(
            name="Pizza Palace",
            description="Authentic Italian pizzas made with traditional recipes and fresh ingredients",
            address="123 Main Street, Downtown",
            phone="(555) 123-4567",
            email="info@pizzapalace.com",
            opening_time=time(11, 0),
            closing_time=time(23, 0),
            delivery_fee=3.99,
            minimum_order=15.00,
            latitude=40.7128,
            longitude=-74.0060
        )

        # Create Burger Barn
        burger_barn = Restaurant.objects.create(
            name="Burger Barn",
            description="Gourmet burgers and classic American comfort food",
            address="456 Oak Avenue, Midtown",
            phone="(555) 987-6543",
            email="orders@burgerbarn.com",
            opening_time=time(10, 0),
            closing_time=time(22, 0),
            delivery_fee=2.99,
            minimum_order=12.00,
            latitude=40.7589,
            longitude=-73.9851
        )

        # Create Sushi Zen
        sushi_zen = Restaurant.objects.create(
            name="Sushi Zen",
            description="Fresh sushi and authentic Japanese cuisine",
            address="789 Cherry Blossom Lane, Uptown",
            phone="(555) 456-7890",
            email="hello@sushizen.com",
            opening_time=time(17, 0),
            closing_time=time(24, 0),
            delivery_fee=4.99,
            minimum_order=20.00,
            latitude=40.7831,
            longitude=-73.9712
        )

        self.stdout.write('Creating categories and menu items...')

        # Pizza Palace Menu
        pizza_appetizers = Category.objects.create(
            restaurant=pizza_palace,
            name="Appetizers",
            description="Perfect starters for your meal",
            display_order=1
        )

        pizza_pizzas = Category.objects.create(
            restaurant=pizza_palace,
            name="Pizzas",
            description="Hand-tossed authentic Italian pizzas",
            display_order=2
        )

        pizza_desserts = Category.objects.create(
            restaurant=pizza_palace,
            name="Desserts",
            description="Sweet endings to your meal",
            display_order=3
        )

        # Pizza Palace Products
        Products.objects.create(
            restaurant=pizza_palace,
            category=pizza_appetizers,
            name="Garlic Bread",
            description="Fresh baked bread with garlic butter and herbs",
            price=6.99,
            preparation_time=10,
            is_vegetarian=True,
            calories=320
        )

        Products.objects.create(
            restaurant=pizza_palace,
            category=pizza_appetizers,
            name="Caesar Salad",
            description="Crisp romaine lettuce with parmesan and croutons",
            price=8.99,
            preparation_time=5,
            is_vegetarian=True,
            calories=280
        )

        Products.objects.create(
            restaurant=pizza_palace,
            category=pizza_pizzas,
            name="Margherita Pizza",
            description="Fresh tomatoes, mozzarella, basil on thin crust",
            price=16.99,
            preparation_time=15,
            is_vegetarian=True,
            spice_level='none',
            calories=890
        )

        Products.objects.create(
            restaurant=pizza_palace,
            category=pizza_pizzas,
            name="Pepperoni Pizza",
            description="Classic pepperoni with mozzarella cheese",
            price=18.99,
            preparation_time=15,
            spice_level='mild',
            calories=1050
        )

        Products.objects.create(
            restaurant=pizza_palace,
            category=pizza_pizzas,
            name="Meat Lovers Pizza",
            description="Pepperoni, sausage, ham, and bacon",
            price=22.99,
            preparation_time=18,
            spice_level='medium',
            calories=1340
        )

        Products.objects.create(
            restaurant=pizza_palace,
            category=pizza_desserts,
            name="Tiramisu",
            description="Classic Italian dessert with coffee and mascarpone",
            price=7.99,
            preparation_time=5,
            is_vegetarian=True,
            calories=450
        )

        # Burger Barn Menu
        burger_appetizers = Category.objects.create(
            restaurant=burger_barn,
            name="Starters",
            description="Tasty appetizers to kick off your meal",
            display_order=1
        )

        burger_burgers = Category.objects.create(
            restaurant=burger_barn,
            name="Burgers",
            description="Handcrafted gourmet burgers",
            display_order=2
        )

        burger_sides = Category.objects.create(
            restaurant=burger_barn,
            name="Sides",
            description="Perfect companions to your burger",
            display_order=3
        )

        # Burger Barn Products
        Products.objects.create(
            restaurant=burger_barn,
            category=burger_appetizers,
            name="Loaded Nachos",
            description="Tortilla chips with cheese, jalapeños, and sour cream",
            price=9.99,
            preparation_time=8,
            is_vegetarian=True,
            spice_level='medium',
            calories=680
        )

        Products.objects.create(
            restaurant=burger_barn,
            category=burger_appetizers,
            name="Buffalo Wings",
            description="Crispy wings tossed in spicy buffalo sauce",
            price=11.99,
            preparation_time=12,
            spice_level='hot',
            calories=520,
            allergens=['gluten']
        )

        Products.objects.create(
            restaurant=burger_barn,
            category=burger_burgers,
            name="Classic Cheeseburger",
            description="Beef patty with cheese, lettuce, tomato, and onion",
            price=13.99,
            preparation_time=12,
            calories=750
        )

        Products.objects.create(
            restaurant=burger_barn,
            category=burger_burgers,
            name="BBQ Bacon Burger",
            description="Beef patty with bacon, BBQ sauce, and onion rings",
            price=16.99,
            preparation_time=15,
            calories=920
        )

        Products.objects.create(
            restaurant=burger_barn,
            category=burger_burgers,
            name="Veggie Burger",
            description="Plant-based patty with avocado and sprouts",
            price=14.99,
            preparation_time=12,
            is_vegetarian=True,
            is_vegan=True,
            calories=580
        )

        Products.objects.create(
            restaurant=burger_barn,
            category=burger_sides,
            name="Sweet Potato Fries",
            description="Crispy sweet potato fries with sea salt",
            price=5.99,
            preparation_time=8,
            is_vegetarian=True,
            is_vegan=True,
            calories=320
        )

        # Sushi Zen Menu
        sushi_appetizers = Category.objects.create(
            restaurant=sushi_zen,
            name="Appetizers",
            description="Traditional Japanese starters",
            display_order=1
        )

        sushi_sushi = Category.objects.create(
            restaurant=sushi_zen,
            name="Sushi & Sashimi",
            description="Fresh fish and expertly prepared sushi",
            display_order=2
        )

        sushi_rolls = Category.objects.create(
            restaurant=sushi_zen,
            name="Specialty Rolls",
            description="Creative and signature sushi rolls",
            display_order=3
        )

        # Sushi Zen Products
        Products.objects.create(
            restaurant=sushi_zen,
            category=sushi_appetizers,
            name="Edamame",
            description="Steamed soybeans with sea salt",
            price=5.99,
            preparation_time=5,
            is_vegetarian=True,
            is_vegan=True,
            calories=120
        )

        Products.objects.create(
            restaurant=sushi_zen,
            category=sushi_appetizers,
            name="Miso Soup",
            description="Traditional soybean paste soup with tofu and seaweed",
            price=4.99,
            preparation_time=5,
            is_vegetarian=True,
            calories=80
        )

        Products.objects.create(
            restaurant=sushi_zen,
            category=sushi_sushi,
            name="Salmon Sashimi",
            description="Fresh Atlantic salmon, 6 pieces",
            price=14.99,
            preparation_time=8,
            is_gluten_free=True,
            calories=240,
            allergens=['fish']
        )

        Products.objects.create(
            restaurant=sushi_zen,
            category=sushi_sushi,
            name="Tuna Nigiri",
            description="Yellowfin tuna over seasoned rice, 4 pieces",
            price=12.99,
            preparation_time=8,
            is_gluten_free=True,
            calories=180,
            allergens=['fish']
        )

        Products.objects.create(
            restaurant=sushi_zen,
            category=sushi_rolls,
            name="California Roll",
            description="Crab, avocado, and cucumber with sesame seeds",
            price=8.99,
            preparation_time=10,
            calories=255,
            allergens=['shellfish']
        )

        Products.objects.create(
            restaurant=sushi_zen,
            category=sushi_rolls,
            name="Dragon Roll",
            description="Eel and cucumber topped with avocado and eel sauce",
            price=16.99,
            preparation_time=15,
            calories=320,
            allergens=['fish']
        )

        Products.objects.create(
            restaurant=sushi_zen,
            category=sushi_rolls,
            name="Spicy Tuna Roll",
            description="Spicy tuna mix with cucumber and spicy mayo",
            price=11.99,
            preparation_time=10,
            spice_level='medium',
            calories=290,
            allergens=['fish']
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created sample data:\n'
                f'- {Restaurant.objects.count()} restaurants\n'
                f'- {Category.objects.count()} categories\n'
                f'- {Products.objects.count()} products'
            )
        )