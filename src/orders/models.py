import uuid
from django.db import models
from django.conf import settings


class Order(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="orders"
    )
    group_order = models.ForeignKey(
        "orders.GroupOrder",
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
    )
    product = models.ForeignKey(
        "products.Product",
        on_delete=models.SET_NULL,
        related_name="orders",
        null=True,
    )
    quantity = models.PositiveIntegerField(default=1)
    price_at_time_of_purchase = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost_of_order = models.DecimalField(max_digits=10, decimal_places=2)
    total_cost_of_order_plus_fees = models.DecimalField(max_digits=10, decimal_places=2)

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("cancelled", "Cancelled"),
        ("delivered", "Delivered"),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order {self.id} by {self.user} for {self.group_order}"


class GroupOrder(models.Model):
    """
    Represents a single batch of group-buying for a product.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(
        "products.Product", on_delete=models.CASCADE, related_name="group_orders"
    )
    batch_number = models.PositiveIntegerField()  # increments with each new batch
    target_quantity = models.PositiveIntegerField()
    current_quantity = models.PositiveIntegerField(default=0)
    deadline = models.DateTimeField(null=True, blank=True)

    STATUS_CHOICES = (
        ("open", "Open"),
        ("closed", "Closed"),  # reached deadline or filled
        ("fulfilled", "Fulfilled"),  # seller shipped
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("product", "batch_number")
        ordering = ["-batch_number"]  # newest batch first

    def __str__(self):
        return f"{self.product.name} - Batch {self.batch_number}"

    # 🔥 helper methods
    def buyers_count(self):
        return self.orders.values("user").distinct().count()

    def total_quantity(self):
        return sum(order.quantity for order in self.orders.all())

    def escrow_amount(self):
        return sum(order.total_cost_of_order for order in self.orders.all())
