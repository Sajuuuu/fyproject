# Pethood E-commerce Project

A Django-based e-commerce platform for pet products with integrated Khalti payment gateway.

## Features

- 🛍️ Product browsing with categories (Food, Clothes, Accessories)
- 🛒 Shopping cart functionality
- 💳 Payment integration (Khalti & Cash on Delivery)
- 👤 User authentication and profile management
- 📦 Order tracking and history
- 📍 Multiple delivery addresses
- 🔍 Product recommendations
- 📱 Responsive design

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Virtual environment (recommended)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone git@github.com:Sajuuuu/fyproject.git
cd fyproject
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate Virtual Environment

**Linux/Mac:**
```bash
source .venv/bin/activate
```

**Windows:**
```bash
.venv\Scripts\activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Environment Configuration

Create a `.env` file in the project root (already exists) and ensure it contains:

```env
# Django Secret Key
SECRET_KEY=your-secret-key-here

# Khalti Payment Gateway (Test/Sandbox Keys)
# Get from: https://test-admin.khalti.com/#/settings/keys
KHALTI_PUBLIC_KEY=20346eb9ec9d4c0bb87cbf7ef0059882
KHALTI_SECRET_KEY=687b9d59675d44d7a45573bac4c54d92
KHALTI_INITIATE_URL=https://dev.khalti.com/api/v2/epayment/initiate/
KHALTI_VERIFY_URL=https://dev.khalti.com/api/v2/epayment/lookup/
```

### 6. Database Setup

```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

Follow the prompts to create an admin account.

### 8. Run Development Server

```bash
python manage.py runserver
```

The application will be available at: **http://localhost:8000**

## Project Structure

```
fyproject/
├── shop/               # Main shop application
├── userauth/           # User authentication & profile
├── dog/                # Additional app
├── src/                # Project settings
├── templates/          # HTML templates
├── static/             # Static files (CSS, JS, images)
├── media/              # User uploaded files
├── db.sqlite3          # SQLite database
├── manage.py           # Django management script
└── requirements.txt    # Python dependencies
```

## Admin Panel

Access the admin panel at: **http://localhost:8000/admin**

Use the superuser credentials you created to log in.

### Admin Features:
- Manage products (add/edit/delete)
- View and update orders
- Manage users
- Configure addresses

## Payment Gateway (Khalti)

### Test Environment Setup

1. The project is configured to use Khalti's test environment
2. Test credentials are already in `.env` file
3. For testing payments, use Khalti test credentials from: https://docs.khalti.com/khalti-epayment/#test-credentials

### Payment Methods Supported:
- **Khalti** - Online payment (E-banking, Mobile Banking, Khalti Wallet)
- **Cash on Delivery (COD)** - Pay when you receive

## Key URLs

- **Home:** http://localhost:8000/
- **Shop:** http://localhost:8000/shop/
- **Cart:** http://localhost:8000/cart/
- **Checkout:** http://localhost:8000/checkout/
- **Profile:** http://localhost:8000/profile/
- **Admin:** http://localhost:8000/admin/

## User Features

### Shopping Flow:
1. Browse products by category
2. Add items to cart with size selection
3. Proceed to checkout
4. Choose saved address or enter new one
5. Select payment method (Khalti or COD)
6. Complete order

### Profile Features:
- View order history with status tracking
- Manage delivery addresses (up to 3)
- Set default address
- Track payment status

## Development

### Running Migrations After Model Changes

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collecting Static Files

```bash
python manage.py collectstatic
```

### Creating Sample Data

Use Django admin panel to add:
- Product categories and sizes
- Sample products with images
- Test orders

## Troubleshooting

### Database Issues
```bash
# Delete database and recreate
rm db.sqlite3
python manage.py migrate
python manage.py createsuperuser
```

### Static Files Not Loading
```bash
python manage.py collectstatic --clear
python manage.py collectstatic
```

### Port Already in Use
```bash
# Run on different port
python manage.py runserver 8080
```

## Git Workflow

### Commit Changes
```bash
git add .
git commit -m "Your commit message"
```

### Push to GitHub (using SSH)
```bash
eval "$(ssh-agent -s)"
ssh-add sajuGithub
git push origin main
```

## Technologies Used

- **Backend:** Django 6.0.1
- **Database:** SQLite3
- **Payment:** Khalti Payment Gateway
- **Frontend:** HTML, CSS, JavaScript
- **Authentication:** Django built-in auth

## License

This project is for educational purposes.

## Support

For issues or questions, contact: Sajupoudel50@gmail.com
