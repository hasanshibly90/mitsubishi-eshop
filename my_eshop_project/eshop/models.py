from django.db import models
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey
from django.utils.text import slugify

class OrderStatus(models.TextChoices):
    PENDING = 'P', 'Pending'
    CONFIRMED = 'C', 'Confirmed'
    CANCELED = 'X', 'Canceled'
    DELIVERED = 'D', 'Delivered'

class Category(MPTTModel):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=150, blank=True, null=True, unique=True)
    parent = TreeForeignKey(
        'self',
        related_name='children',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class MPTTMeta:
        order_insertion_by = ['name']

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug_candidate = base_slug
            counter = 2
            while Category.objects.filter(slug=slug_candidate).exclude(pk=self.pk).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug_candidate
        super().save(*args, **kwargs)

class Banner(models.Model):
    title = models.CharField(max_length=200, blank=True)
    image = models.ImageField(upload_to='banners/', null=True, blank=True)

    def __str__(self):
        return self.title if self.title else "Banner"

class Brand(models.Model):
    name = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='brands/logos/', null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    name = models.CharField("Name", max_length=255)
    original_price = models.DecimalField(max_digits=10, decimal_places=2)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    sku = models.CharField(max_length=50, unique=True)
    image = models.ImageField(upload_to='products/')
    country_of_origin = models.CharField(max_length=100, blank=True, null=True)

    description = models.TextField(blank=True, null=True)
    related_products = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='linked_products'
    )

    # VFD fields
    rated_output_power = models.CharField(max_length=255, blank=True, null=True)
    rated_output_current = models.CharField(max_length=255, blank=True, null=True)
    input_voltage = models.CharField(max_length=255, blank=True, null=True)
    input_frequency = models.CharField(max_length=255, blank=True, null=True)
    output_voltage = models.CharField(max_length=255, blank=True, null=True)
    output_frequency = models.CharField(max_length=255, blank=True, null=True)

    vfd_series = models.CharField(max_length=20, blank=True, null=True)  # e.g., D SERIES, E SERIES
    supply_voltage_ac = models.CharField(max_length=20, blank=True, null=True)
    rated_power_hp = models.DecimalField(max_digits=5, decimal_places=1, blank=True, null=True)
    application = models.CharField(max_length=20, blank=True, null=True)

    # PLC fields
    plc_input = models.CharField("Input (PLC)", max_length=255, blank=True, null=True)
    plc_output = models.CharField("Output (PLC)", max_length=255, blank=True, null=True)
    supply_voltage = models.CharField(max_length=255, blank=True, null=True)
    output_type = models.CharField(max_length=255, blank=True, null=True)

    # HMI fields
    display_device = models.CharField(max_length=255, blank=True, null=True)
    screen_size = models.CharField(max_length=255, blank=True, null=True)
    resolution = models.CharField(max_length=255, blank=True, null=True)
    display_size = models.CharField(max_length=255, blank=True, null=True)
    display_color = models.CharField(max_length=255, blank=True, null=True)
    built_in_interface = models.CharField(max_length=255, blank=True, null=True)

    # SERVO fields
    rated_output = models.CharField(max_length=255, blank=True, null=True)
    rated_torque = models.CharField(max_length=255, blank=True, null=True)
    maximum_torque = models.CharField(max_length=255, blank=True, null=True)
    rated_speed = models.CharField(max_length=255, blank=True, null=True)
    maximum_speed = models.CharField(max_length=255, blank=True, null=True)
    power_supply_capacity = models.CharField(max_length=255, blank=True, null=True)
    power_supply_input = models.CharField(max_length=255, blank=True, null=True)
    rated_voltage = models.CharField(max_length=255, blank=True, null=True)
    rated_current = models.CharField(max_length=255, blank=True, null=True)
    maximum_current = models.CharField(max_length=255, blank=True, null=True)
    control_method = models.CharField(max_length=255, blank=True, null=True)
    dynamic_brake = models.CharField(max_length=255, blank=True, null=True)
    encoder_type = models.CharField(max_length=255, blank=True, null=True)
    communication = models.CharField(max_length=255, blank=True, null=True)
    encoder_resolution = models.CharField(max_length=255, blank=True, null=True)
    servo_motor = models.CharField(max_length=255, blank=True, null=True)
    servo_amplifier = models.CharField(max_length=255, blank=True, null=True)

    dimensions = models.CharField(max_length=255, blank=True, null=True, help_text="(W x H x D in mm)")
    weight = models.CharField(max_length=255, blank=True, null=True)
    compatible_software_package = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Quotation(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=1, choices=OrderStatus.choices, default=OrderStatus.PENDING)
    phone_no = models.CharField(max_length=20, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    delivery_address = models.TextField(blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    order_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"Quotation #{self.pk} for {self.customer_name or 'Anonymous'}"

    def save(self, *args, **kwargs):
        """
        Convert any 'label' values (e.g. 'Confirmed') to the actual code (e.g. 'C')
        so that the database always stores 'C', 'P', 'X', 'D', etc.
        """
        if self.status == 'Pending':
            self.status = OrderStatus.PENDING
        elif self.status == 'Confirmed':
            self.status = OrderStatus.CONFIRMED
        elif self.status == 'Canceled':
            self.status = OrderStatus.CANCELED
        elif self.status == 'Delivered':
            self.status = OrderStatus.DELIVERED

        super().save(*args, **kwargs)

    def compute_total(self):
        total = sum(line.line_total() for line in self.lines.all())
        self.total_amount = total
        self.save(update_fields=['total_amount'])

class QuotationLine(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=25)

    def save(self, *args, **kwargs):
        # Keep existing logic for unit_price
        if self.product and (not self.unit_price or self.unit_price == 0):
            self.unit_price = self.product.original_price

        super().save(*args, **kwargs)

        # Automatically update the Quotation total
        self.quotation.compute_total()

    def delete(self, *args, **kwargs):
        # Capture the Quotation before deleting
        quotation = self.quotation
        super().delete(*args, **kwargs)

        # Recompute total after this line is removed
        quotation.compute_total()

    def line_total(self):
        subtotal = self.quantity * self.unit_price
        discount_amount = subtotal * (self.discount_percent / 100)
        return subtotal - discount_amount

    def __str__(self):
        return f"Line {self.pk} in Quotation #{self.quotation.pk}"


# New Models for Customer and Sales Orders

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_no = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class SalesOrder(models.Model):
    order_number = models.CharField(max_length=50, unique=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pending')

    def __str__(self):
        return self.order_number

class SalesOrderLine(models.Model):
    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='lines')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.product.name} ({self.quantity})"
