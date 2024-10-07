from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from datetime import datetime, timedelta

def dashboard(request):
    context = {
        'user': {
            'first_name': 'John',  # Replace with actual user data
            'profile': {
                'last_updated': datetime.now(),
            }
        },
        'recent_orders_count': 5,  # Replace with actual count
        'wishlist_count': 3,       # Replace with actual count
    }
    return render(request, 'Customer/dashboard.html', context)

def base(request):
    return render(request, 'Customer/base.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, username=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
    return render(request, 'Customer/login.html')

def logout(request):
    auth_logout(request)
    return redirect('login')

def product_details(request):
    # Sample product data - replace with actual database query
    context = {
        'product': {
            'name': 'Fresh Organic Apples',
            'image': {'url': '/static/images/apple.jpg'},
            'freshness_score': 95,
            'brand': 'Organic Farms',
            'expiry_date': datetime.now() + timedelta(days=7),
            'seller': {'company_name': 'Fresh Foods Inc'},
            'description': 'Delicious, crisp organic apples picked fresh from our orchards.'
        },
        'similar_products': [
            {
                'name': 'Organic Oranges',
                'image': {'url': '/static/images/orange.jpg'},
                'price': 4.99,
            },
            # Add more similar products as needed
        ]
    }
    return render(request, 'Customer/product_details.html', context)

def payment_page(request):
    context = {
        'order_items': [
            {'product_name': 'Fresh Organic Apples', 'quantity': 2, 'price': 5.99},
            {'product_name': 'Organic Oranges', 'quantity': 1, 'price': 4.99},
        ],
        'shipping_cost': 5.00,
        'total_amount': 16.97,
    }
    return render(request, 'Customer/payment_page.html', context)

def process_payment(request):
    if request.method == 'POST':
        # Process payment logic here
        return redirect('dashboard')  # Or a success page
    return redirect('payment_page')