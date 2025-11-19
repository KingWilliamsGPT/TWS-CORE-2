import uuid
from django.db import models
from django.conf import settings


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    class SaleType(models.TextChoices):
        RETAIL = "retail", "Retail / Direct Buy"
        DROPSHIPPING = "dropshipping", "Dropshipping / Preorder"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products"
    )
    category = models.ForeignKey(
        "Category", on_delete=models.SET_NULL, null=True, related_name="products"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_type = models.CharField(
        max_length=20,
        choices=SaleType.choices,
        default=SaleType.RETAIL,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    # 🔥 helpers for batch management
    def current_batch(self):
        return self.group_orders.filter(status="open").order_by("-batch_number").first()

    def last_batch(self):
        return (
            self.group_orders.filter(status__in=["closed", "fulfilled"])
            .order_by("-batch_number")
            .first()
        )

    def all_batches(self):
        return self.group_orders.order_by("-batch_number")


class ProductMedia(models.Model):
    MEDIA_TYPES = [
        ("image", "Image"),
        ("video", "Video"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="media"
    )
    file_url = models.URLField()  # Cloudinary
    type = models.CharField(max_length=10, choices=MEDIA_TYPES, default="image")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.type} for {self.product.name}"
