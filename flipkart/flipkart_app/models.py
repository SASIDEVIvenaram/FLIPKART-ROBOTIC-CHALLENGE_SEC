from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings

# Custom User Model
class User(AbstractUser):
    """Custom User model extending AbstractUser to include customer and seller roles."""
    is_customer = models.BooleanField(default=False)
    is_seller = models.BooleanField(default=False)


# User Profile Model
class UserProfile(models.Model):
    """User profile model containing additional information for users."""
    USER_TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('seller', 'Seller'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='customer')
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=6)
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='default_profile.jpg', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile ({self.user_type})"


# Customer Model
class Customer(models.Model):
    """Customer model to track loyalty points and link to user profile."""
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='customer')
    loyalty_points = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Customer: {self.user_profile.user.username}"


# Seller Model
class Seller(models.Model):
    """Seller model to hold seller-specific information."""
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='seller')
    company_name = models.CharField(max_length=200)
    gst_number = models.CharField(max_length=15, unique=True)
    bank_account_number = models.CharField(max_length=20)
    ifsc_code = models.CharField(max_length=11)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.company_name} ({self.user_profile.user.username})"


# Category Model
class Category(models.Model):
    """Category model for product categorization."""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name


# Product Model
class Product(models.Model):
    """Product model representing items available for sale."""
    seller = models.ForeignKey(Seller, on_delete=models.CASCADE, related_name='products')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField()
    image = models.ImageField(upload_to='product_images/')
    is_featured = models.BooleanField(default=False)
    discount_percentage = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def discounted_price(self):
        """Calculates the discounted price based on discount percentage."""
        if self.discount_percentage > 0:
            discount = (self.discount_percentage / 100) * self.price
            return self.price - discount
        return self.price

    def __str__(self):
        return f"{self.name} - by {self.seller.company_name}"


# Cart Model
class Cart(models.Model):
    """Shopping cart model linked to the user."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total(self):
        """Calculates the total price of all items in the cart."""
        return sum(item.get_subtotal() for item in self.items.all())

    def __str__(self):
        return f"{self.user.username}'s Cart"


# Cart Item Model
class CartItem(models.Model):
    """Items in the shopping cart."""
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    def get_subtotal(self):
        """Calculates the subtotal for the item."""
        return self.product.discounted_price() * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


# Order Model
class Order(models.Model):
    """Order model to track user orders."""
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_SHIPPED = 'shipped'
    STATUS_DELIVERED = 'delivered'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_SHIPPED, 'Shipped'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    shipping_address = models.TextField()
    phone_number = models.CharField(max_length=15)
    payment_method = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


# Order Item Model
class OrderItem(models.Model):
    """Items in a specific order."""
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def get_subtotal(self):
        """Calculates the subtotal for the order item."""
        return self.price * self.quantity

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


# Review Model
class Review(models.Model):
    """User reviews for products."""
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s review on {self.product.name}"


# Wishlist Item Model
class WishlistItem(models.Model):
    """Wishlist items for users."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


# Registration Model (Separate from UserProfile)
class Registration(models.Model):
    """Registration model to store registration event details."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='registration')
    date_registered = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Registration"
