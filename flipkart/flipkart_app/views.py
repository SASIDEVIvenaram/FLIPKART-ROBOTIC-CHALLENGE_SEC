from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate
from django.views.generic import ListView, DetailView
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Review, Seller, WishlistItem
from django.contrib.auth.models import User

# Home Page (Product List)
class HomeView(ListView):
    model = Product
    template_name = 'flipkart_app/home.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(stock__gt=0)
        category = self.request.GET.get('category')
        search = self.request.GET.get('search')
        if category:
            queryset = queryset.filter(category__name=category)
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        return context


# Product Detail View
class ProductDetailView(DetailView):
    model = Product
    template_name = 'flipkart_app/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id)[:4]
        context['reviews'] = Review.objects.filter(product=self.object)
        return context


# Add Product to Cart
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, f'{product.name} added to cart.')
    return redirect('cart')


# View Cart
@login_required
def cart_detail(request):
    cart = get_object_or_404(Cart, user=request.user)
    return render(request, 'flipkart_app/cart.html', {'cart': cart})


# Update Cart Item (Increase/Decrease Quantity or Remove)
@login_required
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    action = request.POST.get('action')
    if action == 'increase':
        cart_item.quantity += 1
    elif action == 'decrease':
        cart_item.quantity -= 1
        if cart_item.quantity == 0:
            cart_item.delete()
    elif action == 'remove':
        cart_item.delete()
    else:
        messages.error(request, 'Invalid action.')
    cart_item.save()
    return redirect('cart')


# Checkout View
@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    if cart.items.count() == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('cart')

    if request.method == 'POST':
        shipping_address = request.POST.get('shipping_address')
        phone_number = request.POST.get('phone_number')
        payment_method = request.POST.get('payment_method')
        if not shipping_address or not phone_number or not payment_method:
            messages.error(request, 'Please fill in all required fields.')
            return redirect('checkout')

        # Create the order
        order = Order.objects.create(
            user=request.user,
            shipping_address=shipping_address,
            phone_number=phone_number,
            payment_method=payment_method,
            total_amount=cart.get_total()
        )

        # Move cart items to order items
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                quantity=item.quantity,
                price=item.product.discounted_price(),
            )

        # Clear the cart
        cart.items.all().delete()

        return redirect('order_confirmation', order_id=order.id)

    return render(request, 'flipkart_app/checkout.html', {'cart': cart})


# Order Confirmation View
@login_required
def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'flipkart_app/order_confirmation.html', {'order': order})


# Order History (Customer)
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'flipkart_app/order_history.html', {'orders': orders})


# User Profile View (Customer)
@login_required
def profile(request):
    profile = request.user.profile
    if request.method == 'POST':
        phone_number = request.POST.get('phone_number')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')

        if phone_number and address and city and state and pincode:
            profile.phone_number = phone_number
            profile.address = address
            profile.city = city
            profile.state = state
            profile.pincode = pincode
            profile.save()
            messages.success(request, 'Profile updated successfully.')
        else:
            messages.error(request, 'Please fill in all fields.')
    return render(request, 'flipkart_app/user_profile.html', {'profile': profile})


# Seller Dashboard (Seller-side Order Management)
@login_required
def seller_dashboard(request):
    if not request.user.is_seller:
        messages.error(request, 'You do not have permission to view this page.')
        return redirect('home')

    seller = request.user.seller
    # Fetch orders containing products sold by this seller
    orders = Order.objects.filter(items__product__seller=seller).distinct()

    return render(request, 'flipkart_app/seller_dashboard.html', {'orders': orders})


# User Registration View (Simplified without forms)
def user_register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email is already in use.')
            return redirect('register')

        user = User.objects.create_user(username=username, email=email, password=password)
        messages.success(request, 'Registration successful! You can now log in.')
        return redirect('login')

    return render(request, 'flipkart_app/register.html')


# User Login View (Simplified)
def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')

    return render(request, 'flipkart_app/login.html')


# User Logout View
@login_required
def user_logout(request):
    logout(request)
    return redirect('home')


# Wishlist View
@login_required
def wishlist(request):
    wishlist_items = WishlistItem.objects.filter(user=request.user)
    return render(request, 'flipkart_app/wishlist.html', {'wishlist_items': wishlist_items})


# Add to Wishlist
@login_required
def add_to_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    WishlistItem.objects.get_or_create(user=request.user, product=product)
    messages.success(request, f'{product.name} added to your wishlist.')
    return redirect('wishlist')


# Remove from Wishlist
@login_required
def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    WishlistItem.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f'{product.name} removed from your wishlist.')
    return redirect('wishlist')
