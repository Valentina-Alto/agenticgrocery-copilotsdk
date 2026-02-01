# SmartShop - AI-Powered Supermarket Shopping Assistant

A conversational shopping experience powered by CopilotClient, where customers receive personalized product recommendations and can manage their shopping cart through natural language interaction.

## Features

### 🛒 Smart Shopping
- **User Authentication**: Three mock customer profiles with distinct preferences
- **Personalized Recommendations**: AI agent recommends products based on customer preferences, dietary restrictions, and favorite brands
- **Dynamic Cart Management**: Cart automatically populates based on agent recommendations and user requests
- **Real-time Cart Updates**: Shopping cart synchronizes with conversation

### 💬 Conversational Interface
- **CopilotClient Integration**: GPT-4 powered AI assistant using Microsoft Copilot SDK
- **Smart Tool Usage**: Agent has access to 4 specialized tools:
  - Get Product Recommendations (filtered by customer profile)
  - Search Products (by name or category)
  - Get Product Details (with active offers)
  - Manage Cart (add/remove/update items)

### 🎁 Special Offers
- Real-time promotions across categories:
  - 30% off Organic Produce
  - Buy 2 Get 1 Free on Whole Grains
  - Loyalty Bonuses ($10 off $50+)
  - Premium Protein Sales
  - Dairy Deals
- Agent proactively suggests relevant offers


## Architecture

### Backend (Python/Flask)
- **app.py**: Main Flask application with:
  - Session management (Flask-Session)
  - CopilotClient initialization with per-user sessions
  - Mock data (customers, products, offers)
  - RESTful API endpoints
  - Tool implementations using Pydantic models

### Frontend (HTML/CSS/JavaScript)
- **pwsh.html**: Single-page application with:
  - Login screen with customer selection
  - Split-view chat interface
  - Real-time shopping cart sidebar
  - Responsive design with green theme


## Data Models

### Product
```python
{
    'id': str,
    'name': str,
    'category': str,
    'price': float,
    'qty_unit': str,
    'organic': bool
}
```

### Customer
```python
{
    'name': str,
    'preferences': list[str],
    'dietary_restrictions': list[str],
    'favorite_brands': list[str],
    'typical_budget': float,
    'shopping_frequency': str
}
```

### Special Offer
```python
{
    'id': str,
    'title': str,
    'description': str,
    'discount_percent': float,
    'discount_amount': float,
    'applicable_products': list[str],
    'valid_until': str,
    'category': str
}
```

## Installation & Setup

### Prerequisites
- Python 3.8+
- CopilotClient SDK installed
- Local CopilotClient instance running on `localhost:4321`

### Installation
```bash
pip install -r requirements.txt
```

### Running the Application
```bash
python app.py
```
The app will start on `http://localhost:5001`




## Technologies
- **Backend**: Flask, Python, CopilotClient SDK, Pydantic
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Sessions**: Flask-Session (filesystem)
- **AI Model**: GPT-4.1 via Copilot SDK

## Notes
- All data is in-memory (session-based)
- Cart persists only during user session
- No external database dependencies for demo purposes
- Requires active CopilotClient on localhost:4321
