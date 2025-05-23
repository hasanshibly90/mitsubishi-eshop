from .models import Customer, SalesOrder, SalesOrderLine

def create_customer_and_sales_order(order):
    """
    Creates (or retrieves) a Customer and converts the given Quotation (order)
    into a Sales Order along with its Sales Order Lines.
    """
    # 1) Ensure there's a valid email (fallback if blank):
    email_value = order.email or f"anon-{order.pk}@example.com"

    customer, _ = Customer.objects.get_or_create(
        email=email_value,
        defaults={
            'name': order.customer_name or 'Anonymous',
            'phone_no': order.phone_no,
            'address': order.delivery_address,
        }
    )

    # 2) Create or update the SalesOrder
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
        # If it already exists, update the main fields
        sales_order.customer = customer
        sales_order.total_amount = order.total_amount
        sales_order.status = 'Confirmed'
        sales_order.save(update_fields=['customer', 'total_amount', 'status'])
        # Optionally clear existing lines
        sales_order.lines.all().delete()

    # 3) Copy QuotationLine to SalesOrderLine
    for line in order.lines.all():
        SalesOrderLine.objects.create(
            sales_order=sales_order,
            product=line.product,
            quantity=line.quantity,
            unit_price=line.unit_price,
            discount_percent=line.discount_percent
        )

    return sales_order
