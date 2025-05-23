import json
import requests
from django import forms
from django.contrib import admin, messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.shortcuts import redirect, get_object_or_404
from django.urls import path
from django.utils.html import format_html
from django.utils import timezone

from mptt.admin import DraggableMPTTAdmin

from .models import (
    Category, Banner, Brand, Product,
    Quotation, QuotationLine, OrderStatus,
    # Make sure Customer, SalesOrder, SalesOrderLine are also imported
    Customer, SalesOrder, SalesOrderLine
)

###############################################################################
# 0) LOCAL HELPER: CREATE/UPDATE CUSTOMER & SALES ORDER
###############################################################################
def create_customer_and_sales_order(order):
    """
    Creates (or retrieves) a local Customer and converts the given Quotation (order)
    into a local Sales Order along with its Sales Order Lines.
    """
    # 1) Ensure we have a valid email (fallback if blank)
    email_value = order.email or f"anon-{order.pk}@example.com"

    # 2) Get or create the local Customer
    customer, _ = Customer.objects.get_or_create(
        email=email_value,
        defaults={
            'name': order.customer_name or 'Anonymous',
            'phone_no': order.phone_no,
            'address': order.delivery_address,
        }
    )

    # 3) Create or update the SalesOrder based on order_number
    sales_order, created = SalesOrder.objects.get_or_create(
        order_number=order.order_number,
        defaults={
            'customer': customer,
            'total_amount': order.total_amount,
            'created_at': order.created_at,
            'status': 'Confirmed',
        }
    )

    if not created:
        # If SalesOrder already exists, update it
        sales_order.customer = customer
        sales_order.total_amount = order.total_amount
        sales_order.status = 'Confirmed'
        sales_order.save(update_fields=['customer', 'total_amount', 'status'])
        # Optionally clear existing lines before re-adding them
        sales_order.lines.all().delete()

    # 4) Create SalesOrderLine for each QuotationLine
    for line in order.lines.all():
        SalesOrderLine.objects.create(
            sales_order=sales_order,
            product=line.product,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percent=line.discount_percent
        )

    return sales_order

###############################################################################
# 1) PRODUCT-FORM-RELATED CONFIG
###############################################################################
GLOBAL_MANDATORY = {
    "category",
    "brand",
    "name",  # Name is required in the form, but no longer enforced unique in DB
    "original_price",
    "sku",
    "image",
    "country_of_origin",
}

GLOBAL_OPTIONAL = {
    # e.g. "discounted_price", "related_products", etc.
}

# --- VFD_OPTIONAL includes rated_output_current ---
VFD_OPTIONAL = {
    "description", "rated_output_power", "rated_output_current", "input_voltage",
    "input_frequency", "output_voltage", "output_frequency", "dimensions",
    "weight", "compatible_software_package", "related_products",
    # VFD filter fields:
    "vfd_series", "supply_voltage_ac", "rated_power_hp", "application",
}

PLC_OPTIONAL = {
    "description", "plc_input", "plc_output", "supply_voltage", "output_type",
    "dimensions", "weight", "compatible_software_package", "related_products",
}

HMI_OPTIONAL = {
    "description", "display_device", "screen_size", "resolution", "display_size",
    "display_color", "built_in_interface", "supply_voltage",
    "dimensions", "weight", "compatible_software_package", "related_products",
}

SERVO_OPTIONAL = {
    "description", "rated_output", "rated_torque", "maximum_torque", "rated_speed",
    "maximum_speed", "power_supply_capacity", "power_supply_input",
    "rated_voltage", "rated_current", "maximum_current", "control_method",
    "dynamic_brake", "encoder_type", "communication", "encoder_resolution",
    "servo_motor", "servo_amplifier",
    "dimensions", "weight", "compatible_software_package", "related_products",
}

CATEGORY_RULES = {
    "VFD": {
        "mandatory": set(),
        "optional": VFD_OPTIONAL,
        "hidden": set(),
    },
    "PLC": {
        "mandatory": set(),
        "optional": PLC_OPTIONAL,
        "hidden": set(),
    },
    "HMI": {
        "mandatory": set(),
        "optional": HMI_OPTIONAL,
        "hidden": set(),
    },
    "SERVO": {
        "mandatory": set(),
        "optional": SERVO_OPTIONAL,
        "hidden": set(),
    },
}

###############################################################################
# 2) DYNAMIC PRODUCT FORM
###############################################################################
class DynamicProductForm(forms.ModelForm):
    """
    A single ModelForm that conditionally shows/hides fields depending on
    the top-level category (VFD, PLC, HMI, SERVO).
    Also, certain VFD fields become dropdowns with a blank placeholder.
    """

    # VFD filter fields as dropdowns:
    VFD_SERIES_CHOICES = [
        ("", "---------"),
        ("D SERIES", "D SERIES"),
        ("E SERIES", "E SERIES"),
        ("F SERIES", "F SERIES"),
        ("A SERIES", "A SERIES"),
    ]
    vfd_series = forms.ChoiceField(choices=VFD_SERIES_CHOICES, required=False)

    SUPPLY_VOLTAGE_AC_CHOICES = [
        ("", "---------"),
        ("1 PHASE 200VAC", "1 PHASE 200VAC"),
        ("3 PHASE 200VAC", "3 PHASE 200VAC"),
        ("3 PHASE 400VAC", "3 PHASE 400VAC"),
    ]
    supply_voltage_ac = forms.ChoiceField(choices=SUPPLY_VOLTAGE_AC_CHOICES, required=False)

    RATED_POWER_HP_CHOICES = [
        ("", "---------"),
        ("0.4", "0.4 kW"),
        ("0.75", "0.75 kW"),
        ("1.5", "1.5 kW"),
        ("2.2", "2.2 kW"),
        ("3.7", "3.7 kW"),
        ("5.5", "5.5 kW"),
        ("7.5", "7.5 kW"),
        ("11.0", "11 kW"),
        ("15.0", "15 kW"),
        ("18.5", "18.5 kW"),
        ("22.0", "22 kW"),
        ("30.0", "30 kW"),
        ("37.0", "37 kW"),
        ("45.0", "45 kW"),
        ("55.0", "55 kW"),
        ("75.0", "75 kW"),
        ("90.0", "90 kW"),
        ("110.0", "110 kW"),
        ("132.0", "132 kW"),
        ("160.0", "160 kW"),
        ("185.0", "185 kW"),
        ("220.0", "220 kW"),
        ("250.0", "250 kW"),
        ("280.0", "280 kW"),
        ("315.0", "315 kW"),
        ("355.0", "355 kW"),
        ("400.0", "400 kW"),
    ]
    rated_power_hp = forms.ChoiceField(choices=RATED_POWER_HP_CHOICES, required=False)

    APPLICATION_CHOICES = [
        ("", "---------"),
        ("Heavy Duty (HD)", "Heavy Duty (HD)"),
        ("Normal Duty (ND)", "Normal Duty (ND)"),
    ]
    application = forms.ChoiceField(choices=APPLICATION_CHOICES, required=False)

    # RATED CURRENT (A) CHOICES for the new dropdown field:
    RATED_CURRENT_A_CHOICES = [
        ("", "---------"),
        ("1.2A", "1.2A"),
        ("1.6A", "1.6A"),
        ("2.2A", "2.2A"),
        ("2.3A", "2.3A"),
        ("2.5A", "2.5A"),
        ("2.6A", "2.6A"),
        ("3A", "3A"),
        ("3.6A", "3.6A"),
        ("3.8A", "3.8A"),
        ("4A", "4A"),
        ("4.2A", "4.2A"),
        ("4.6A", "4.6A"),
        ("5A", "5A"),
        ("5.2A", "5.2A"),
        ("6A", "6A"),
        ("7A", "7A"),
        ("7.7A", "7.7A"),
        ("8A", "8A"),
        ("8.3A", "8.3A"),
        ("9.5A", "9.5A"),
        ("10A", "10A"),
        ("10.5A", "10.5A"),
        ("11A", "11A"),
        ("12A", "12A"),
        ("12.6A", "12.6A"),
        ("16A", "16A"),
        ("16.5A", "16.5A"),
        ("16.7A", "16.7A"),
        ("17A", "17A"),
        ("17.5A", "17.5A"),
        ("23A", "23A"),
        ("23.8A", "23.8A"),
        ("24A", "24A"),
        ("25A", "25A"),
        ("29.5A", "29.5A"),
        ("30A", "30A"),
        ("31A", "31A"),
        ("31.8A", "31.8A"),
        ("33A", "33A"),
        ("34A", "34A"),
        ("38A", "38A"),
        ("45A", "45A"),
        ("47A", "47A"),
        ("49A", "49A"),
        ("58A", "58A"),
        ("60A", "60A"),
        ("62A", "62A"),
        ("63A", "63A"),
        ("77A", "77A"),
        ("93A", "93A"),
        ("116A", "116A"),
        ("180A", "180A"),
        ("216A", "216A"),
        ("260A", "260A"),
        ("325A", "325A"),
        ("361A", "361A"),
        ("432A", "432A"),
        ("481A", "481A"),
        ("547A", "547A"),
        ("610A", "610A"),
        ("683A", "683A"),
        ("770A", "770A"),
        ("866A", "866A"),
        ("962A", "962A"),
    ]
    # We store the chosen rated current value in the existing DB field "rated_output_current"
    rated_output_current = forms.ChoiceField(
        choices=RATED_CURRENT_A_CHOICES,
        required=False
    )

    class Meta:
        model = Product
        fields = [
            "category", "brand", "name", "original_price", "sku", "image",
            "country_of_origin", "discounted_price", "description", "related_products",
            "rated_output_power", "rated_output_current", "input_voltage",
            "input_frequency", "output_voltage", "output_frequency",
            "dimensions", "weight", "compatible_software_package",
            # Overridden above: vfd_series, supply_voltage_ac, rated_power_hp, application,
            # and now rated_output_current is used for the new dropdown field
            "plc_input", "plc_output", "supply_voltage", "output_type",
            "display_device", "screen_size", "resolution", "display_size",
            "display_color", "built_in_interface",
            "rated_output", "rated_torque", "maximum_torque", "rated_speed",
            "maximum_speed", "power_supply_capacity", "power_supply_input",
            "rated_voltage", "rated_current", "maximum_current", "control_method",
            "dynamic_brake", "encoder_type", "communication", "encoder_resolution",
            "servo_motor", "servo_amplifier",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Change label from "Model Name" to "Name" and keep it required
        if "name" in self.fields:
            self.fields["name"].label = "Name"
            self.fields["name"].required = True

        # Show SKU in the "related_products" box
        if "related_products" in self.fields:
            self.fields["related_products"].label_from_instance = lambda obj: obj.sku

        # Identify the top-level category
        category_obj = None
        if self.instance and self.instance.pk and self.instance.category:
            category_obj = self.instance.category
        else:
            cat_id = self.data.get("category") or self.initial.get("category")
            if cat_id:
                from .models import Category
                try:
                    category_obj = Category.objects.get(pk=cat_id)
                except Category.DoesNotExist:
                    category_obj = None

        # Merge sets
        final_mandatory = set(GLOBAL_MANDATORY)
        final_optional = set(GLOBAL_OPTIONAL)
        final_hidden = set()

        if category_obj:
            ancestors = category_obj.get_ancestors(include_self=True)
            for cat in ancestors:
                cat_key = cat.name.upper()  # e.g. "VFD"
                if cat_key in CATEGORY_RULES:
                    conf = CATEGORY_RULES[cat_key]
                    final_mandatory |= conf.get("mandatory", set())
                    final_optional |= conf.get("optional", set())
                    final_hidden |= conf.get("hidden", set())
                    break

        # Hide any fields not recognized
        all_fields = set(self.fields.keys())
        recognized = final_mandatory | final_optional | final_hidden
        leftover = all_fields - recognized
        final_hidden |= leftover

        for fname in list(self.fields.keys()):
            if fname in final_hidden:
                self.fields.pop(fname, None)

        # Mark mandatory vs optional (ensure "name" stays required)
        for fname, field in self.fields.items():
            field.required = (fname in final_mandatory or fname == "name")


###############################################################################
# 3) CATEGORY, BANNER, BRAND ADMIN
###############################################################################
@admin.register(Category)
class CategoryAdmin(DraggableMPTTAdmin):
    list_display = ("tree_actions", "indented_title", "parent")
    list_display_links = ("indented_title",)


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title",)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("name", "description")


###############################################################################
# 4) PRODUCT ADMIN (Dynamic + Clone)
###############################################################################
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = DynamicProductForm
    change_form_template = "admin/eshop/product/change_form.html"

    list_display = (
        "name",   # name can be duplicated
        "sku",    # SKU remains unique
        "original_price",
        "discounted_price",
        "category",
        "brand",
        "clone_link"
    )
    filter_horizontal = ("related_products",)

    def get_form_kwargs(self, request, obj=None):
        if request.method == "POST":
            return {"data": request.POST, "files": request.FILES, "instance": obj}
        return {"instance": obj}

    def get_fieldsets(self, request, obj=None):
        """
        We separate fields into:
         1) Mandatory Fields
         2) Filter Settings (VFD)
         3) Optional Fields
        """
        form_class = super().get_form(request, obj, fields=None)
        form_kwargs = self.get_form_kwargs(request, obj)
        form_instance = form_class(**form_kwargs)

        mandatory_fields = []
        optional_fields = []
        for fname, field in form_instance.fields.items():
            if field.required:
                mandatory_fields.append(fname)
            else:
                optional_fields.append(fname)

        # The "Filter Settings (VFD)" fields
        FILTER_FIELD_NAMES = (
            "vfd_series",
            "supply_voltage_ac",
            "rated_power_hp",
            "rated_output_current",  # Ensure it is recognized
            "application"
        )

        filter_fields = []
        for ff in FILTER_FIELD_NAMES:
            if ff in form_instance.fields:
                filter_fields.append(ff)
                if ff in mandatory_fields:
                    mandatory_fields.remove(ff)
                if ff in optional_fields:
                    optional_fields.remove(ff)

        # Place "related_products" last
        ALWAYS_LAST = ("related_products",)
        normal_optional = [f for f in optional_fields if f not in ALWAYS_LAST]
        last_block = [f for f in optional_fields if f in ALWAYS_LAST]
        optional_fields = normal_optional + last_block

        fieldsets = []
        if mandatory_fields:
            fieldsets.append(("Mandatory Fields", {"fields": mandatory_fields}))

        # Show the VFD fields in a fieldset (removing "collapse" if you want them always visible)
        if filter_fields:
            fieldsets.append(
                ("Filter Settings (VFD)", {
                    "fields": filter_fields,
                    # "classes": ("collapse",),  # Optionally remove 'collapse' to see them immediately
                })
            )

        if optional_fields:
            fieldsets.append(
                ("Optional Fields", {
                    "fields": optional_fields,
                    "classes": ("collapse",),
                })
            )

        return fieldsets

    def get_urls(self):
        """Add a custom URL for cloning products by SKU."""
        urls = super().get_urls()
        custom_urls = [
            path(
                "<int:product_id>/clone/",
                self.admin_site.admin_view(self.clone_view),
                name="eshop_product_clone"
            ),
        ]
        return custom_urls + urls

    def clone_view(self, request, product_id):
        """
        Cloning logic:
          - Only new SKU is required.
          - Name can remain the same as the original.
        """
        new_sku = request.GET.get("sku", "").strip()
        if not new_sku:
            messages.error(request, "SKU is required to clone the product.")
            return redirect(request.META.get("HTTP_REFERER", "admin:index"))
        if Product.objects.filter(sku=new_sku).exists():
            messages.error(request, f"A product with SKU '{new_sku}' already exists.")
            return redirect(request.META.get("HTTP_REFERER", "admin:index"))

        original_product = get_object_or_404(Product, pk=product_id)
        old_related = original_product.related_products.all()

        # Copy the product
        original_product.pk = None
        original_product.sku = new_sku

        try:
            original_product.save()
        except IntegrityError as e:
            messages.error(request, f"Integrity error while saving clone: {str(e)}")
            return redirect(request.META.get("HTTP_REFERER", "admin:index"))

        # Preserve M2M relationships
        original_product.related_products.set(old_related)
        messages.success(
            request,
            f"Product cloned successfully with Name '{original_product.name}' and SKU '{new_sku}'."
        )
        return redirect(f"../../{original_product.pk}/change/")

    def clone_link(self, obj):
        url = f"{obj.pk}/clone/"
        return format_html(
            '<a href="{}" onclick="return promptCloneNameAndSKU(this);">Clone</a>',
            url
        )
    clone_link.short_description = "Clone"


###############################################################################
# 5) ACCOUNTING API INTEGRATION
###############################################################################
def _compute_final_customer_name(q):
    if q.customer_name:
        return q.customer_name
    phone = q.phone_no or ""
    last6 = phone[-6:] if len(phone) >= 6 else phone
    return f"Customer # {last6}"


def find_existing_customer_in_accounting_by_name(name_to_check):
    url = "https://acc.aiosol.io/api2/customers/"
    headers = {
        "Accept": "application/json",
        "X-API-KEY": "CgRERU1PEhIJAnrzI5egzkURl2LZU3OI5xUaEgndVzUL4yiPQRGt0qpiCi1Wcg=="
    }
    resp = requests.get(url, headers=headers)
    if resp.status_code not in [200, 201]:
        raise Exception(f"Error listing customers: {resp.status_code} - {resp.text}")

    data = resp.json()
    if isinstance(data, dict):
        data = [data]
    for cust in data:
        if isinstance(cust, dict) and cust.get("name") == name_to_check:
            return cust.get("key")
    return None


def create_customer_in_accounting(order):
    final_name = _compute_final_customer_name(order)
    existing_key = find_existing_customer_in_accounting_by_name(final_name)
    if existing_key:
        return existing_key

    billing_addr = order.delivery_address or ""
    delivery_addr = order.delivery_address or ""
    email_value = order.email or ""
    phone = order.phone_no or ""

    payload = {
        "Name": final_name,
        "BillingAddress": billing_addr,
        "DeliveryAddress": delivery_addr,
        "Email": email_value,
        "CustomFields": {},
        "CustomFields2": {
            "Strings": {},
            "Decimals": {},
            "Dates": {},
            "Booleans": {},
            "StringArrays": {}
        }
    }
    if phone:
        payload["CustomFields2"]["Strings"]["f732a914-f5ca-4e3b-bba2-70198f5e6b75"] = phone

    url = "https://acc.aiosol.io/api2/customer-form"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "CgRERU1PEhIJAnrzI5egzkURl2LZU3OI5xUaEgndVzUL4yiPQRGt0qpiCi1Wcg=="
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code in [200, 201]:
        data = resp.json()
        return data.get("Key")
    else:
        raise Exception(f"Error creating customer: {resp.text}")


def get_inventory_item_key(sku):
    url = "https://acc.aiosol.io/api2/inventory-items/"
    headers = {
        "Accept": "application/json",
        "X-API-KEY": "CgRERU1PEhIJAnrzI5egzkURl2LZU3OI5xUaEgndVzUL4yiPQRGt0qpiCi1Wcg=="
    }
    response = requests.get(url, headers=headers)
    if response.status_code in [200, 201]:
        data = response.json()
        if isinstance(data, dict) and "inventoryItems" in data:
            inventory_items = data["inventoryItems"]
        elif isinstance(data, list):
            inventory_items = data
        else:
            raise Exception(f"Unexpected format for inventory items: {data}")

        for item in inventory_items:
            if str(item.get("itemCode", "")) == str(sku):
                return item.get("key")

        raise Exception(f"Error finding inventory item for SKU {sku} in accounting.")
    else:
        raise Exception(f"Error retrieving inventory items: {response.text}")


def create_sales_order_in_accounting(customer_key, order):
    lines_payload = []
    has_discount = False

    for line in order.lines.all():
        discount_val = float(line.discount_percent or 0)
        if discount_val > 0:
            has_discount = True

        item_key = get_inventory_item_key(line.product.sku)
        line_payload = {
            "Item": item_key,
            "LineDescription": line.product.name,
            "CustomFields": {},
            "CustomFields2": {
                "Strings": {},
                "Decimals": {},
                "Dates": {},
                "Booleans": {},
                "StringArrays": {}
            },
            "Qty": float(line.quantity),
            "SalesUnitPrice": float(line.unit_price),
            "DiscountPercentage": discount_val
        }
        lines_payload.append(line_payload)

    payload = {
        "Date": order.created_at.strftime("%Y-%m-%dT00:00:00"),
        "Reference": order.order_number,
        "Customer": customer_key,
        "Lines": lines_payload,
        "Discount": has_discount,
        "SalesOrderFooters": [],
        "CustomFields": {},
        "CustomFields2": {
            "Strings": {},
            "Decimals": {},
            "Dates": {},
            "Booleans": {},
            "StringArrays": {}
        }
    }
    url = "https://acc.aiosol.io/api2/sales-order-form"
    headers = {
        "Content-Type": "application/json",
        "X-API-KEY": "CgRERU1PEhIJAnrzI5egzkURl2LZU3OI5xUaEgndVzUL4yiPQRGt0qpiCi1Wcg=="
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code in [200, 201]:
        data = resp.json()
        return data.get("Key")
    else:
        raise Exception(f"Error creating sales order: {resp.text}")


def confirm_orders_in_accounting(modeladmin, request, queryset):
    for order in queryset:
        if order.status != OrderStatus.CONFIRMED:
            try:
                customer_key = create_customer_in_accounting(order)
                so_key = create_sales_order_in_accounting(customer_key, order)
                order.status = OrderStatus.CONFIRMED
                order.save(update_fields=["status"])
                messages.success(
                    request,
                    f"Order {order.order_number} confirmed. Sales Order Key: {so_key}"
                )
            except Exception as e:
                messages.error(
                    request,
                    f"Error posting order {order.order_number} to accounting: {str(e)}"
                )
confirm_orders_in_accounting.short_description = "Confirm selected orders in Accounting"


###############################################################################
# 6) QUOTATION ADMIN
###############################################################################
class QuotationLineInline(admin.TabularInline):
    model = QuotationLine
    extra = 0
    can_delete = True
    fields = ("product", "quantity", "unit_price", "discount_percent", "description")
    readonly_fields = ("unit_price",)

    def has_add_permission(self, request, obj):
        # If you want to allow adding lines from inline, remove this return False
        return False


@admin.register(Quotation)
class QuotationAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer_name",
        "phone_no",
        "email",
        "total_amount",
        "status",
        "created_at",
    )
    list_filter = ("status", "created_at")
    search_fields = (
        "order_number", "phone_no", "delivery_address",
        "customer__username", "customer__email", "customer_name",
    )
    actions = [confirm_orders_in_accounting]
    inlines = [QuotationLineInline]

    fieldsets = (
        ("Customer Info", {
            "fields": (
                ("customer", "customer_name"),
                ("phone_no", "email"),
                "delivery_address",
            )
        }),
        ("Order Info", {
            "fields": ("order_number", "subject", "status")
        }),
        ("Totals", {
            "fields": ("total_amount", "created_at")
        }),
    )
    readonly_fields = ("created_at", "total_amount")

    def save_model(self, request, obj, form, change):
        if not obj.order_number:
            generated_order_number = "ORD" + timezone.now().strftime("%Y%m%d%H%M%S")
            obj.order_number = generated_order_number
            if not obj.subject:
                obj.subject = (
                    f"Discount Request for order no: {generated_order_number} "
                    f"on {timezone.now().strftime('%Y-%m-%d')}"
                )
        old_status = None
        if obj.pk:
            old_instance = Quotation.objects.filter(pk=obj.pk).first()
            if old_instance:
                old_status = old_instance.status

        super().save_model(request, obj, form, change)

        # 1) If status changed to CONFIRMED, create local Customer & SalesOrder
        if old_status != OrderStatus.CONFIRMED and obj.status == OrderStatus.CONFIRMED:
            # Create or update local DB records
            create_customer_and_sales_order(obj)

            # 2) Attempt to push to external accounting
            try:
                ckey = create_customer_in_accounting(obj)
                so_key = create_sales_order_in_accounting(ckey, obj)
                messages.success(
                    request,
                    f"Successfully posted Quotation {obj.order_number} to accounting. "
                    f"Sales Order Key={so_key}"
                )
            except Exception as e:
                # If external push fails, revert the status
                obj.status = old_status
                obj.save(update_fields=["status"])
                messages.error(
                    request,
                    f"Error posting order {obj.order_number} to accounting: {str(e)}"
                )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        quotation = form.instance
        quotation.compute_total()
        quotation.save(update_fields=["total_amount"])


@admin.register(QuotationLine)
class QuotationLineAdmin(admin.ModelAdmin):
    list_display = ("quotation", "product", "quantity", "unit_price", "discount_percent")
