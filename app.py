import asyncio
import json
from flask import Flask, render_template, request, jsonify, session
from flask_session import Session
from copilot import CopilotClient
from copilot.tools import define_tool
from pydantic import BaseModel, Field
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supermarket-demo-key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# ===== MOCK DATA =====

MOCK_CUSTOMERS = {
    'sarah_johnson': {
        'name': 'Sarah Johnson',
        'preferences': ['organic', 'gluten-free', 'dairy-free'],
        'dietary_restrictions': ['gluten-free', 'vegan'],
        'favorite_brands': ['Whole Foods', 'Nature Valley'],
        'typical_budget': 80,
        'shopping_frequency': 'weekly'
    },
    'mike_chen': {
        'name': 'Mike Chen',
        'preferences': ['budget-friendly', 'bulk deals', 'frozen meals'],
        'dietary_restrictions': [],
        'favorite_brands': ['Great Value', 'Lean Cuisine'],
        'typical_budget': 60,
        'shopping_frequency': 'bi-weekly'
    },
    'emma_patel': {
        'name': 'Emma Patel',
        'preferences': ['premium', 'organic', 'healthy'],
        'dietary_restrictions': ['vegetarian'],
        'favorite_brands': ['Organic Valley', 'Vital Farms'],
        'typical_budget': 120,
        'shopping_frequency': 'weekly'
    }
}

MOCK_PRODUCTS = {
    'bananas': {'id': 'bananas', 'name': 'Bananas (bunch)', 'category': 'produce', 'price': 1.99, 'qty_unit': 'bunch', 'organic': True},
    'apples': {'id': 'apples', 'name': 'Gala Apples', 'category': 'produce', 'price': 4.99, 'qty_unit': 'lb', 'organic': True},
    'broccoli': {'id': 'broccoli', 'name': 'Fresh Broccoli', 'category': 'produce', 'price': 2.49, 'qty_unit': 'head', 'organic': True},
    'chicken_breast': {'id': 'chicken_breast', 'name': 'Chicken Breast (3 lbs)', 'category': 'meat', 'price': 12.99, 'qty_unit': 'pack', 'organic': False},
    'salmon': {'id': 'salmon', 'name': 'Wild Salmon Fillet', 'category': 'meat', 'price': 18.99, 'qty_unit': 'lb', 'organic': True},
    'whole_milk': {'id': 'whole_milk', 'name': 'Organic Whole Milk (1 gal)', 'category': 'dairy', 'price': 5.99, 'qty_unit': 'gallon', 'organic': True},
    'greek_yogurt': {'id': 'greek_yogurt', 'name': 'Greek Yogurt (32 oz)', 'category': 'dairy', 'price': 6.49, 'qty_unit': 'container', 'organic': False},
    'cheddar_cheese': {'id': 'cheddar_cheese', 'name': 'Cheddar Cheese (1 lb)', 'category': 'dairy', 'price': 7.99, 'qty_unit': 'pack', 'organic': False},
    'whole_wheat_bread': {'id': 'whole_wheat_bread', 'name': 'Whole Wheat Bread', 'category': 'bakery', 'price': 3.49, 'qty_unit': 'loaf', 'organic': True},
    'brown_rice': {'id': 'brown_rice', 'name': 'Brown Rice (2 lb)', 'category': 'pantry', 'price': 4.49, 'qty_unit': 'bag', 'organic': True},
    'pasta': {'id': 'pasta', 'name': 'Whole Wheat Pasta (1 lb)', 'category': 'pantry', 'price': 2.99, 'qty_unit': 'box', 'organic': False},
    'olive_oil': {'id': 'olive_oil', 'name': 'Extra Virgin Olive Oil (25.5 oz)', 'category': 'pantry', 'price': 14.99, 'qty_unit': 'bottle', 'organic': True},
    'almond_butter': {'id': 'almond_butter', 'name': 'Natural Almond Butter (12 oz)', 'category': 'pantry', 'price': 8.99, 'qty_unit': 'jar', 'organic': True},
    'coffee': {'id': 'coffee', 'name': 'Fair Trade Coffee (1 lb)', 'category': 'beverages', 'price': 10.99, 'qty_unit': 'bag', 'organic': True},
    'orange_juice': {'id': 'orange_juice', 'name': 'Fresh Orange Juice (64 oz)', 'category': 'beverages', 'price': 5.99, 'qty_unit': 'bottle', 'organic': True},
    'water_bottles': {'id': 'water_bottles', 'name': 'Sparkling Water (12-pack)', 'category': 'beverages', 'price': 6.99, 'qty_unit': 'pack', 'organic': False},
}

MOCK_SPECIAL_OFFERS = [
    {
        'id': 'offer_1',
        'title': '30% off Organic Produce',
        'description': 'Get 30% off all organic fruits and vegetables this week!',
        'discount_percent': 30,
        'applicable_products': ['bananas', 'apples', 'broccoli'],
        'valid_until': '2026-02-06',
        'category': 'produce'
    },
    {
        'id': 'offer_2',
        'title': 'Buy 2 Get 1 Free - Whole Grains',
        'description': 'Buy 2 get 1 free on all brown rice, pasta, and whole wheat products',
        'discount_percent': 33,
        'applicable_products': ['brown_rice', 'pasta', 'whole_wheat_bread'],
        'valid_until': '2026-02-03',
        'category': 'pantry'
    },
    {
        'id': 'offer_3',
        'title': 'Loyalty Bonus: $10 off on $50 purchase',
        'description': 'Spend $50 and get $10 off at checkout',
        'discount_amount': 10,
        'min_purchase': 50,
        'valid_until': '2026-02-10',
        'category': 'general'
    },
    {
        'id': 'offer_4',
        'title': 'Premium Proteins Sale',
        'description': 'Save on Wild Salmon and Organic Chicken this week',
        'discount_percent': 25,
        'applicable_products': ['salmon', 'chicken_breast'],
        'valid_until': '2026-02-05',
        'category': 'meat'
    },
    {
        'id': 'offer_5',
        'title': 'Dairy Deal: $5 off $20 in dairy',
        'description': 'Spend $20 on dairy products and get $5 off',
        'discount_amount': 5,
        'min_purchase': 20,
        'category_filter': 'dairy',
        'valid_until': '2026-02-08',
        'category': 'dairy'
    }
]

# ===== TOOL DEFINITIONS =====

# Global cart storage (synced with Flask session)
global_carts = {}

class GetProductRecommendationsParams(BaseModel):
    customer_id: str = Field(description="The customer ID or username")
    include_offers: bool = Field(default=True, description="Whether to include current special offers in recommendations")

class SearchProductsParams(BaseModel):
    query: str = Field(description="Product name or category to search for")
    limit: int = Field(default=10, description="Maximum number of results to return")

class GetProductDetailsParams(BaseModel):
    product_id: str = Field(description="The product ID")

class ManageCartParams(BaseModel):
    action: str = Field(description="'add', 'remove', or 'update'")
    product_id: str = Field(description="The product ID or product name")
    quantity: float = Field(default=1, description="The quantity to add or update")
    customer_id: str = Field(description="The customer ID")

# ===== HELPER FUNCTIONS =====

def get_recommendations_for_customer(customer_id: str, include_offers: bool = True) -> dict:
    """Helper function to get recommendations - can be used directly without tool decoration"""
    customer_id = customer_id.lower().replace(' ', '_')
    
    if customer_id not in MOCK_CUSTOMERS:
        # Try to find by name if direct lookup fails
        for cust_id, cust_data in MOCK_CUSTOMERS.items():
            if cust_data['name'].lower() == customer_id.lower():
                customer_id = cust_id
                break
        else:
            return {'success': False, 'error': f'Customer {customer_id} not found.'}
    
    customer = MOCK_CUSTOMERS[customer_id]
    recommendations = []
    
    # Filter products based on preferences
    for product_id, product in MOCK_PRODUCTS.items():
        score = 0
        
        # Boost organic products if customer prefers organic
        if 'organic' in customer['preferences'] and product.get('organic'):
            score += 10
        
        # Check if product matches dietary restrictions
        if 'gluten-free' in customer['dietary_restrictions'] and product.get('gluten_free'):
            score += 5
        
        if 'vegetarian' in customer['dietary_restrictions'] and product['category'] != 'meat':
            score += 2
        
        # Check if product is from favorite brands
        for brand in customer['favorite_brands']:
            if brand.lower() in product['name'].lower():
                score += 8
        
        if score > 0:
            recommendations.append({
                'product_id': product_id,
                'name': product['name'],
                'price': product['price'],
                'category': product['category'],
                'match_score': score
            })
    
    # Add offers if requested
    offers = []
    if include_offers:
        for offer in MOCK_SPECIAL_OFFERS:
            if offer['valid_until'] >= datetime.now().strftime('%Y-%m-%d'):
                offers.append({
                    'title': offer['title'],
                    'description': offer['description'],
                    'applicable_products': offer.get('applicable_products', [])
                })
    
    return {
        'success': True,
        'customer_name': customer['name'],
        'recommendations': sorted(recommendations, key=lambda x: x['match_score'], reverse=True)[:8],
        'active_offers': offers,
        'suggested_budget': customer['typical_budget']
    }

@define_tool(description="Get personalized product recommendations based on customer profile and preferences")
async def get_product_recommendations_tool(params: GetProductRecommendationsParams) -> dict:
    """Returns recommended products based on customer profile, dietary preferences, and current offers"""
    return get_recommendations_for_customer(params.customer_id, params.include_offers)

@define_tool(description="Search for products in the supermarket catalog")
async def search_products_tool(params: SearchProductsParams) -> dict:
    """Search products by name or category"""
    query = params.query.lower()
    limit = params.limit
    
    results = []
    for product_id, product in MOCK_PRODUCTS.items():
        if query in product['name'].lower() or query in product['category'].lower():
            results.append({
                'product_id': product_id,
                'name': product['name'],
                'price': product['price'],
                'category': product['category']
            })
    
    return {
        'success': True,
        'query': query,
        'results': results[:limit],
        'total_found': len(results)
    }

@define_tool(description="Get detailed information about a specific product")
async def get_product_details_tool(params: GetProductDetailsParams) -> dict:
    """Returns full product details including price, category, organic status, etc."""
    product_id = params.product_id
    
    if product_id not in MOCK_PRODUCTS:
        return {'success': False, 'error': f'Product {product_id} not found'}
    
    product = MOCK_PRODUCTS[product_id]
    
    # Check if product has active offers
    active_offers = []
    for offer in MOCK_SPECIAL_OFFERS:
        if product_id in offer.get('applicable_products', []):
            if offer['valid_until'] >= datetime.now().strftime('%Y-%m-%d'):
                active_offers.append({
                    'title': offer['title'],
                    'discount_percent': offer.get('discount_percent'),
                    'discount_amount': offer.get('discount_amount')
                })
    
    return {
        'success': True,
        'product': product,
        'active_offers': active_offers,
        'in_stock': True
    }

@define_tool(description="Manage shopping cart items")
async def manage_cart_tool(params: ManageCartParams) -> dict:
    """Add, remove, or update items in the shopping cart"""
    action = params.action.lower()
    product_id = params.product_id
    quantity = max(1, params.quantity)  # Ensure quantity is at least 1
    customer_id = params.customer_id.lower().replace(' ', '_')
    
    # Try to find product by ID or name
    if product_id not in MOCK_PRODUCTS:
        # Search by product name (case-insensitive)
        search_term = product_id.lower()
        for pid, product in MOCK_PRODUCTS.items():
            if search_term in product['name'].lower():
                product_id = pid
                break
        else:
            return {'success': False, 'error': f'Product "{product_id}" not found in catalog'}
    
    if action not in ['add', 'remove', 'update']:
        return {'success': False, 'error': 'Action must be "add", "remove", or "update"'}
    
    try:
        # Initialize cart for customer if not exists
        if customer_id not in global_carts:
            global_carts[customer_id] = {}
        
        cart = global_carts[customer_id]
        product = MOCK_PRODUCTS[product_id]
        
        if action == 'add':
            current_qty = cart.get(product_id, 0)
            cart[product_id] = current_qty + quantity
            return {
                'success': True,
                'action': 'added',
                'product_name': product['name'],
                'quantity': quantity,
                'new_total': cart[product_id],
                'product_id': product_id
            }
        elif action == 'remove':
            if product_id in cart:
                del cart[product_id]
            return {
                'success': True,
                'action': 'removed',
                'product_name': product['name'],
                'product_id': product_id
            }
        elif action == 'update':
            if quantity <= 0:
                if product_id in cart:
                    del cart[product_id]
            else:
                cart[product_id] = quantity
            return {
                'success': True,
                'action': 'updated',
                'product_name': product['name'],
                'new_quantity': quantity,
                'product_id': product_id
            }
    except Exception as e:
        return {'success': False, 'error': f'Error managing cart: {str(e)}'}

# ===== SESSION MANAGEMENT =====

# Global session and client per user
clients = {}
sessions = {}
session_timestamps = {}
loop = None
SESSION_TIMEOUT = 600  # 10 minutes in seconds

async def init_client_for_user(user_id, force_refresh=False):
    """Initialize CopilotClient for a specific user"""
    import time
    
    # Check if session exists and hasn't timed out
    if user_id in sessions and not force_refresh:
        last_access = session_timestamps.get(user_id, time.time())
        if time.time() - last_access < SESSION_TIMEOUT:
            session_timestamps[user_id] = time.time()
            return sessions[user_id]
    
    # Create new session
    try:
        client = CopilotClient(options={"cli_url": "localhost:4321"})
        customer = MOCK_CUSTOMERS.get(user_id, {})
        
        system_context = f"""You are a helpful supermarket shopping assistant for SmartShop.
You are assisting a logged-in customer. The customer ID will be provided in every message.
IMPORTANT: Always extract and use the Customer ID from messages in the [Current Customer ID: ...] format.

YOUR BEHAVIOR:
1. When customer asks for recommendations, FIRST call get_product_recommendations_tool with their customer ID
2. IMMEDIATELY after getting recommendations, ADD EVERY SINGLE ITEM to the cart:
   - For EACH recommended product in the results:
     * Call manage_cart_tool 
     * Set action="add"
     * Set product_id to the exact product_id from recommendations (e.g., "bananas", "apples", "salmon")
     * Set quantity=1
     * Set customer_id to the value from [Current Customer ID: ...]
   - DO THIS FOR EVERY ITEM IN THE RECOMMENDATIONS - no exceptions
   - Make separate manage_cart_tool calls for each product (don't try to add multiple in one call)
3. After all items are added, send a summary message that:
   - Lists what you added (e.g., "✓ Added Bananas, ✓ Added Gala Apples, ✓ Added Fresh Broccoli...")
   - Shows the product scores from recommendations
   - Highlights relevant special offers

CRITICAL INSTRUCTIONS:
- ALWAYS call manage_cart_tool for each recommended product - this is mandatory
- Use exact product_id values like "bananas", "apples", "salmon", "chicken_breast", etc.
- Pass customer_id correctly - extract it from [Current Customer ID: ...] in the message
- Do NOT ask permission - just add items and confirm
- Items MUST be added to cart - the user expects to see them populate in the sidebar
- If customer mentions a product they're interested in, also add it to cart with manage_cart_tool"""
        
        clients[user_id] = client
        sessions[user_id] = await client.create_session({
            "model": "gpt-4.1",
            "streaming": False,
            "system": system_context,
            "tools": [
                get_product_recommendations_tool,
                search_products_tool,
                get_product_details_tool,
                manage_cart_tool
            ],
        })
        session_timestamps[user_id] = time.time()
        return sessions[user_id]
    except Exception as e:
        print(f"Error creating session for {user_id}: {str(e)}")
        raise

async def get_chat_response(user_id, user_message):
    """Get response from CopilotClient for a user"""
    max_retries = 2
    for attempt in range(max_retries):
        try:
            session_obj = await init_client_for_user(user_id, force_refresh=(attempt > 0))
            # Inject customer ID into message to ensure agent has it
            customer = MOCK_CUSTOMERS.get(user_id, {})
            enriched_message = f"""[Current Customer ID: {user_id}]
[Customer Name: {customer.get('name', 'Unknown')}]

User Message: {user_message}"""
            response = await session_obj.send_and_wait({"prompt": enriched_message})
            return response.data.content
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying with fresh session...")
                continue
            else:
                raise

def run_async(coro):
    global loop
    if loop is None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

# ===== ROUTES =====

@app.route('/')
def index():
    return render_template('pwsh.html')

@app.route('/api/login', methods=['POST'])
def login():
    """Handle user login"""
    try:
        data = request.json
        customer_id = data.get('customer_id', '')
        
        if customer_id not in MOCK_CUSTOMERS:
            return jsonify({'error': 'Invalid customer ID'}), 401
        
        customer = MOCK_CUSTOMERS[customer_id]
        session['customer_id'] = customer_id
        session['customer_name'] = customer['name']
        session['cart'] = {}
        session.modified = True
        
        return jsonify({
            'success': True,
            'customer_name': customer['name'],
            'message': f"Welcome {customer['name']}! Let's start shopping."
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    """Handle user logout"""
    customer_id = session.get('customer_id')
    if customer_id:
        # Clean up session from global storage
        if customer_id in sessions:
            del sessions[customer_id]
        if customer_id in clients:
            del clients[customer_id]
        if customer_id in session_timestamps:
            del session_timestamps[customer_id]
        if customer_id in global_carts:
            del global_carts[customer_id]
    
    session.clear()
    return jsonify({'success': True})

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        if 'customer_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.json
        user_message = data.get('message', '')
        customer_id = session['customer_id']
        
        response = run_async(get_chat_response(customer_id, user_message))
        
        # Auto-populate cart if user is asking for recommendations
        if any(word in user_message.lower() for word in ['recommend', 'suggest', 'what do you recommend', 'what would you suggest']):
            # Get recommendations and auto-add to cart
            try:
                recommendations_response = get_recommendations_for_customer(customer_id, include_offers=True)
                
                if recommendations_response.get('success'):
                    # Auto-add all recommended products to cart
                    if customer_id not in global_carts:
                        global_carts[customer_id] = {}
                    
                    cart = global_carts[customer_id]
                    for rec in recommendations_response.get('recommendations', []):
                        product_id = rec.get('product_id')
                        if product_id:
                            # Add 1 of each recommended item
                            current_qty = cart.get(product_id, 0)
                            cart[product_id] = current_qty + 1
                            
            except Exception as e:
                print(f"Error auto-adding recommendations: {str(e)}")
        
        # Sync global cart with Flask session
        if customer_id in global_carts:
            session['cart'] = global_carts[customer_id]
            session.modified = True
        
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/cart', methods=['GET'])
def get_cart():
    """Get current shopping cart"""
    try:
        if 'customer_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        cart = session.get('cart', {})
        cart_items = []
        total = 0
        
        for product_id, quantity in cart.items():
            product = MOCK_PRODUCTS.get(product_id)
            if product:
                item_total = product['price'] * quantity
                total += item_total
                cart_items.append({
                    'product_id': product_id,
                    'name': product['name'],
                    'price': product['price'],
                    'quantity': quantity,
                    'subtotal': item_total
                })
        
        return jsonify({
            'success': True,
            'items': cart_items,
            'total': round(total, 2),
            'item_count': len(cart_items)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/cart/remove', methods=['POST'])
def remove_from_cart():
    """Remove an item from the shopping cart"""
    try:
        if 'customer_id' not in session:
            return jsonify({'error': 'Not authenticated'}), 401
        
        data = request.json
        product_id = data.get('product_id', '')
        customer_id = session['customer_id']
        
        # Remove from global carts
        if customer_id in global_carts and product_id in global_carts[customer_id]:
            del global_carts[customer_id][product_id]
        
        # Remove from session cart
        if 'cart' in session and product_id in session['cart']:
            del session['cart'][product_id]
            session.modified = True
        
        return jsonify({'success': True, 'message': f'Item removed from cart'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/customers', methods=['GET'])
def get_customers():
    """Get list of available customers for login (demo only)"""
    customers = [
        {'id': 'sarah_johnson', 'name': 'Sarah Johnson'},
        {'id': 'mike_chen', 'name': 'Mike Chen'},
        {'id': 'emma_patel', 'name': 'Emma Patel'}
    ]
    return jsonify({'customers': customers})

if __name__ == '__main__':
    app.run(debug=False, port=5001)
