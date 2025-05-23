import os
import json
from decimal import Decimal
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse
from django.template.loader import render_to_string
from django.http import JsonResponse
import pdfkit

##############################
# PAGINATION IMPORT
##############################
from django.core.paginator import Paginator

from django.db.models import Q, CharField
from django.db.models.functions import Cast

# Merged import: extra models for Customer and SalesOrder functionality
from .models import Category, Banner, Brand, Product, Quotation, Customer, SalesOrder, SalesOrderLine
from .forms import (
    BrandForm,
    QuotationHeaderForm,
    QuotationLineFormSet,   # extra=0 in forms.py to avoid auto blank line
    OrderUpdateForm
)

# Import external accounting integration functions from admin.py
from .admin import create_customer_in_accounting, create_sales_order_in_accounting

def create_customer_and_sales_order(order):
    """
    Creates (or retrieves) a Customer and converts the given Quotation (order)
    into a local Sales Order along with its Sales Order Lines.
    """
    # Use a fallback email if order.email is blank
    email_value = order.email or f"anon-{order.pk}@example.com"
    
    # Get or create the customer record
    customer, _ = Customer.objects.get_or_create(
        email=email_value,
        defaults={
            'name': order.customer_name or 'Anonymous',
            'phone_no': order.phone_no,
            'address': order.delivery_address,
        }
    )
    
    # Use get_or_create to avoid UNIQUE constraint error on order_number
    sales_order, created = SalesOrder.objects.get_or_create(
        order_number=order.order_number,
        defaults={
            'customer': customer,
            'total_amount': order.total_amount,
            'created_at': order.created_at,
            'status': 'Confirmed',  # Adjust as needed
        }
    )
    
    if not created:
        # If the SalesOrder already exists, update its details
        sales_order.customer = customer
        sales_order.total_amount = order.total_amount
        sales_order.status = 'Confirmed'
        sales_order.save(update_fields=['customer', 'total_amount', 'status'])
        # Optionally clear existing SalesOrderLines before re-adding them
        sales_order.lines.all().delete()
    
    # Create SalesOrderLine for each QuotationLine
    for line in order.lines.all():
        SalesOrderLine.objects.create(
            sales_order=sales_order,
            product=line.product,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percent=line.discount_percent
        )
    return sales_order

def home_view(request):
    categories = Category.objects.filter(parent__isnull=True)
    banner = Banner.objects.first()

    # Retrieve up to 8 products for each major category:
    vfd_products = Product.objects.filter(category__name__iexact='VFD').order_by('-id')[:8]
    plc_products = Product.objects.filter(category__name__iexact='PLC').order_by('-id')[:8]
    hmi_products = Product.objects.filter(category__name__iexact='HMI').order_by('-id')[:8]
    servo_products = Product.objects.filter(category__name__iexact='SERVO').order_by('-id')[:8]

    # Fetch top-level category objects (grandparents) so we can pass along their children
    vfd_grandparent = Category.objects.filter(name__iexact='VFD').first()
    parent_categories = vfd_grandparent.children.all() if vfd_grandparent else []

    plc_grandparent = Category.objects.filter(name__iexact='PLC').first()
    plc_parent_categories = plc_grandparent.children.all() if plc_grandparent else []

    hmi_grandparent = Category.objects.filter(name__iexact='HMI').first()
    hmi_parent_categories = hmi_grandparent.children.all() if hmi_grandparent else []

    servo_grandparent = Category.objects.filter(name__iexact='SERVO').first()
    servo_parent_categories = servo_grandparent.children.all() if servo_grandparent else []

    return render(request, 'home.html', {
        'categories': categories,
        'banner': banner,
        'vfd_products': vfd_products,
        'plc_products': plc_products,
        'hmi_products': hmi_products,
        'servo_products': servo_products,
        # For the "series cards" sections in home.html
        'parent_categories': parent_categories,
        'plc_parent_categories': plc_parent_categories,
        'hmi_parent_categories': hmi_parent_categories,
        'servo_parent_categories': servo_parent_categories,
    })

def parent_detail_view(request, parent_slug):
    parent_cat = get_object_or_404(Category, slug=parent_slug)
    children = parent_cat.children.all()

    if children.exists():
        data = []
        for child_cat in children:
            all_subcats = child_cat.get_descendants(include_self=True)
            child_products = Product.objects.filter(category__in=all_subcats).order_by('-id')[:4]
            data.append({
                'child_cat': child_cat,
                'child_products': child_products,
            })
        return render(request, 'parent_detail.html', {
            'parent_cat': parent_cat,
            'data': data,
            'has_children': True,
        })
    else:
        all_subcats = parent_cat.get_descendants(include_self=True)
        parent_products = Product.objects.filter(category__in=all_subcats).order_by('-id')[:4]
        return render(request, 'parent_detail.html', {
            'parent_cat': parent_cat,
            'parent_products': parent_products,
            'has_children': False,
        })

def product_detail_view(request, sku):
    if not sku or sku.lower() == 'none':
        return redirect('home')
    product = get_object_or_404(Product, sku=sku)
    return render(request, 'product_detail.html', {'product': product})

def fx_series_view(request):
    return render(request, 'fx_series.html')

def vfd_view(request):
    return render(request, 'vfd.html')

def category_filter_view(request, cat_name):
    category = get_object_or_404(Category, name__iexact=cat_name)
    all_cats = category.get_descendants(include_self=True)
    products_list = Product.objects.filter(category__in=all_cats).order_by('-id')

    paginator = Paginator(products_list, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'category_filter.html', {
        'cat_name': category.name,
        'page_obj': page_obj,
    })

def series_filter_view(request, series_name):
    products_list = Product.objects.filter(series__iexact=series_name).order_by('-id')
    paginator = Paginator(products_list, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'series_filter.html', {
        'series_name': series_name,
        'page_obj': page_obj,
    })

def all_vfd_inverters_view(request):
    vfd_cat = get_object_or_404(Category, name__iexact='VFD')
    subparents = vfd_cat.children.all()
    sections = []
    for parent_cat in subparents:
        all_subcats = parent_cat.get_descendants(include_self=True)
        parent_products = Product.objects.filter(category__in=all_subcats).order_by('-id')[:4]
        sections.append({
            'parent_cat': parent_cat,
            'products': parent_products,
        })
    return render(request, 'all_vfd_inverters.html', {'sections': sections})

def brand_detail_view(request, brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    return render(request, 'brand_detail.html', {'brand': brand})

def search_view(request):
    """
    Modified so that the main text box searches by SKU (instead of product name).
    Additional filters (vfd_series, supply_voltage_ac, rated_power_hp, 
    rated_current_a, application) still apply.
    """
    query = request.GET.get('q', '').strip()

    # Read additional filter parameters
    vfd_series_filter = request.GET.get('vfd_series', '').strip()
    supply_voltage_ac_filter = request.GET.get('supply_voltage_ac', '').strip()
    rated_power_hp_filter = request.GET.get('rated_power_hp', '').strip()
    rated_current_a_filter = request.GET.get('rated_current_a', '').strip()
    application_filter = request.GET.get('application', '').strip()

    # Start with all products
    products = Product.objects.all()

    # 1) If user typed something, filter by SKU__icontains
    if query:
        products = products.filter(sku__icontains=query)

    # 2) Apply the dropdown filters
    if vfd_series_filter:
        products = products.filter(vfd_series__iexact=vfd_series_filter)

    if supply_voltage_ac_filter:
        products = products.filter(supply_voltage_ac__iexact=supply_voltage_ac_filter)

    if rated_power_hp_filter:
        try:
            numeric_value = Decimal(rated_power_hp_filter.replace("kW", "").strip())
            products = products.filter(rated_power_hp=numeric_value)
        except:
            pass

    if rated_current_a_filter:
        products = products.filter(rated_output_current__iexact=rated_current_a_filter)

    if application_filter:
        products = products.filter(application__iexact=application_filter)

    return render(request, 'search.html', {
        'query': query,
        'products': products,
        # So the dropdowns remain selected after search
        'selected_vfd_series': vfd_series_filter,
        'selected_supply_voltage_ac': supply_voltage_ac_filter,
        'selected_rated_power_hp': rated_power_hp_filter,
        'selected_rated_current_a': rated_current_a_filter,
        'selected_application': application_filter,
    })

def product_filter_search_view(request):
    search_query = request.GET.get('q', '')
    capacity_filter = request.GET.get('capacity', '')
    voltage_type_filter = request.GET.get('voltage_type', '')
    series_filter = request.GET.get('series', '')

    capacities = Product.objects.exclude(capacity__isnull=True).exclude(capacity__exact='') \
                                .values_list('capacity', flat=True).distinct()
    voltage_types = Product.objects.exclude(voltage_type__isnull=True).exclude(voltage_type__exact='') \
                                   .values_list('voltage_type', flat=True).distinct()
    series_list = Product.objects.exclude(series__isnull=True).exclude(series__exact='') \
                                 .values_list('series', flat=True).distinct()

    products = Product.objects.all()
    if search_query:
        products = products.filter(name__icontains=search_query)
    if capacity_filter:
        products = products.filter(capacity=capacity_filter)
    if voltage_type_filter:
        products = products.filter(voltage_type=voltage_type_filter)
    if series_filter:
        products = products.filter(series=series_filter)

    context = {
        'products': products,
        'search_query': search_query,
        'capacity_filter': capacity_filter,
        'voltage_type_filter': voltage_type_filter,
        'series_filter': series_filter,
        'capacities': capacities,
        'voltage_types': voltage_types,
        'series_list': series_list,
    }
    return render(request, 'product_filter_search.html', context)

def product_search_suggestions(request):
    term = request.GET.get('term', '')
    product_names = Product.objects.filter(name__icontains=term).values_list('name', flat=True)[:10]
    suggestions = [{'label': name, 'value': name} for name in product_names]
    return JsonResponse(suggestions, safe=False)

@login_required
def ask_for_discount_view(request, sku):
    product = get_object_or_404(Product, sku=sku)
    product_prices = {str(p.pk): str(p.original_price) for p in Product.objects.all()}
    product_prices_json = json.dumps(product_prices)

    if request.method == "POST":
        new_quote = Quotation()
        header_form = QuotationHeaderForm(request.POST, instance=new_quote)
        formset = QuotationLineFormSet(request.POST, instance=new_quote, prefix="lines")

        if header_form.is_valid() and formset.is_valid():
            new_quote = header_form.save(commit=False)
            new_quote.customer = request.user
            if not new_quote.customer_name and new_quote.phone_no:
                last6 = new_quote.phone_no[-6:] if len(new_quote.phone_no) >= 6 else new_quote.phone_no
                new_quote.customer_name = f"Customer #{last6}"

            generated_order_number = "ORD" + timezone.now().strftime("%Y%m%d%H%M%S")
            new_quote.order_number = generated_order_number
            new_quote.subject = (
                f"Discount Request for order no: {generated_order_number} on "
                f"{timezone.now().strftime('%Y-%m-%d')}"
            )
            # Do NOT set status to 'C' here; leave it pending for manual confirmation
            new_quote.save()
            formset.save()
            if hasattr(new_quote, "compute_total"):
                new_quote.compute_total()

            # Do not call create_customer_and_sales_order(new_quote) here,
            # so that the discount request remains pending and is not auto-confirmed.
            # The admin can later confirm the order manually.

            pdf_file_path, pdf_file_name = generate_pdf_file(new_quote)
            shareable_file_url = os.path.join(settings.MEDIA_URL, "quotations", pdf_file_name)
            subject_email = f"Discount request for {product.name}"
            body = (
                f"User {request.user} requested a multi-line discount.\n"
                f"Quotation ID: {new_quote.pk}\n\n"
                f"Please find the attached PDF for full details."
            )
            email = EmailMessage(
                subject=subject_email,
                body=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[settings.DEFAULT_FROM_EMAIL],
            )
            email.attach_file(pdf_file_path)
            email.send()

            messages.success(
                request,
                f"Your discount request for Order No: {new_quote.order_number} has been successfully submitted and is pending confirmation! A PDF has been emailed."
            )
            request.session['shareable_file_url'] = shareable_file_url
            return redirect("discount_submitted", quotation_id=new_quote.pk)
        else:
            return render(request, "new_discount.html", {
                "header_form": header_form,
                "formset": formset,
                "product_prices_json": product_prices_json,
            })
    else:
        new_quote = Quotation()
        header_form = QuotationHeaderForm(instance=new_quote)
        formset = QuotationLineFormSet(
            instance=new_quote,
            prefix="lines",
            initial=[{
                "product": product.pk,
                "quantity": 1,
                "unit_price": product.original_price,
                "discount_percent": 25
            }]
        )
        return render(request, "new_discount.html", {
            "header_form": header_form,
            "formset": formset,
            "product_prices_json": product_prices_json,
        })

def generate_pdf_file(quotation):
    html_string = render_to_string('quotation_pdf.html', {'quotation': quotation})
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    file_name = f"quotation_{quotation.pk}_{timestamp}.pdf"
    quotations_dir = os.path.join(settings.MEDIA_ROOT, "quotations")
    os.makedirs(quotations_dir, exist_ok=True)
    file_path = os.path.join(quotations_dir, file_name)

    config = pdfkit.configuration(wkhtmltopdf=r'C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe')
    pdfkit.from_string(html_string, file_path, configuration=config)

    return file_path, file_name

@staff_member_required
def order_management_view(request):
    orders = Quotation.objects.all().order_by("-created_at")
    status_filter = request.GET.get("status")
    if status_filter:
        orders = orders.filter(status=status_filter)
    context = {"orders": orders}
    return TemplateResponse(request, "order_management.html", context)

@staff_member_required
def edit_order_view(request, pk):
    order = get_object_or_404(Quotation, pk=pk)
    product_prices_json = json.dumps({
        str(p.pk): str(p.original_price) for p in Product.objects.all()
    })

    if request.method == "POST":
        form = OrderUpdateForm(request.POST, instance=order)
        formset = QuotationLineFormSet(request.POST, instance=order, prefix="lines")
        if form.is_valid() and formset.is_valid():
            form.save()  # Save changes to Quotation (status, etc.)
            formset.save()  # Save changes to QuotationLine (quantity, discount, etc.)

            # Recompute total_amount from all lines
            order.compute_total()

            # NEW: If order is confirmed, create/update local Customer and Sales Order,
            # and push to external accounting.
            if order.status == 'C':
                create_customer_and_sales_order(order)
                try:
                    ckey = create_customer_in_accounting(order)
                    so_key = create_sales_order_in_accounting(ckey, order)
                    messages.success(
                        request,
                        f"Order posted to external accounting. Sales Order Key: {so_key}"
                    )
                except Exception as e:
                    messages.error(
                        request,
                        f"Error posting order {order.order_number} to accounting: {str(e)}"
                    )

            messages.success(request, "Order updated successfully!")
            return redirect("order_management")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = OrderUpdateForm(instance=order)
        formset = QuotationLineFormSet(instance=order, prefix="lines")

    return render(request, "order_edit.html", {
        "form": form,
        "formset": formset,
        "order": order,
        "product_prices_json": product_prices_json,  # for auto-fill in new lines
    })

def quotation_detail_view(request, pk):
    quotation = get_object_or_404(Quotation, pk=pk)
    lines = quotation.lines.all()

    pdf_file_path, pdf_file_name = generate_pdf_file(quotation)
    shareable_file_url = os.path.join(settings.MEDIA_URL, "quotations", pdf_file_name)

    return render(request, "quotation_detail.html", {
        "quotation": quotation,
        "lines": lines,
        "shareable_file_url": shareable_file_url,
    })

@login_required
def discount_submitted_view(request, quotation_id):
    quotation = get_object_or_404(Quotation, pk=quotation_id)
    product = quotation.lines.first().product if quotation.lines.exists() else None
    shareable_file_url = request.session.get('shareable_file_url', None)
    return render(request, "discount_submitted.html", {
        "quotation": quotation,
        "product": product,
        "shareable_file_url": shareable_file_url,
    })

###############################################
# API-Like VIEWS for Dependent Dropdowns
###############################################
def top_level_categories_view(request):
    if request.method == 'GET':
        top_cats = Category.objects.filter(parent__isnull=True).order_by('name')
        data = [{'id': c.id, 'name': c.name} for c in top_cats]
        return JsonResponse(data, safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)

def category_children_view(request, parent_id):
    if request.method == 'GET':
        subcats = Category.objects.filter(parent_id=parent_id).order_by('name')
        data = [{'id': c.id, 'name': c.name} for c in subcats]
        return JsonResponse(data, safe=False)
    return JsonResponse({'error': 'Method not allowed'}, status=405)
