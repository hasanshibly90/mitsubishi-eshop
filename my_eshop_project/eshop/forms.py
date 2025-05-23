from decimal import Decimal
from django import forms
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
import sys

from .models import Brand, Product, Quotation, QuotationLine

ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/gif']

##############################
# Brand Form (unchanged)
##############################
class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'logo', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:
            if logo.content_type not in ALLOWED_IMAGE_TYPES:
                raise ValidationError('Only JPEG, PNG, or GIF files are allowed for logos.')
        return logo


##############################
# BaseProductForm
##############################
class BaseProductForm(forms.ModelForm):
    """
    - brand, name (model name), original_price, sku, image => MANDATORY
    - country_of_origin also treated as mandatory (see clean()).
    - image must be a valid content type (JPEG, PNG, GIF).
    """
    class Meta:
        model = Product
        fields = '__all__'  # We'll exclude category-specific fields in the specialized forms.

    def clean_image(self):
        image = self.cleaned_data.get('image')
        if image:
            if image.content_type not in ALLOWED_IMAGE_TYPES:
                raise ValidationError('Only JPEG, PNG, or GIF files are allowed for product images.')
        return image

    def clean(self):
        cleaned_data = super().clean()
        # Mandatory for ANY product:
        mandatory_fields = [
            'brand',
            'name',              # "Model Name"
            'original_price',
            'sku',
            'image',
            'country_of_origin', # Also required for all categories
        ]
        for f in mandatory_fields:
            if not cleaned_data.get(f):
                self.add_error(f, f"{f} is mandatory for all product categories.")
        return cleaned_data


##############################
# Specialized Product Forms
##############################
class VFDProductForm(BaseProductForm):
    class Meta(BaseProductForm.Meta):
        exclude = [
            # PLC
            'plc_input', 'plc_output', 'supply_voltage', 'output_type',
            # HMI
            'display_device', 'screen_size', 'external_dimensions',
            'resolution', 'display_size', 'display_color',
            'built_in_interface', 'weight', 'compatible_software_package',
            # SERVO
            'rated_torque', 'maximum_torque', 'rated_speed', 'maximum_speed',
            'power_supply_capacity', 'power_supply_input', 'rated_voltage',
            'rated_current', 'maximum_current', 'control_method', 'dynamic_brake',
            'encoder_type', 'communication', 'encoder_resolution', 'servo_motor',
            'servo_amplifier',
        ]


class PLCProductForm(BaseProductForm):
    class Meta(BaseProductForm.Meta):
        exclude = [
            # VFD
            'rated_output_power', 'rated_output_current', 'input_voltage',
            'input_frequency', 'output_frequency_range', 'output_voltage', 'dimensions',
            # HMI
            'display_device', 'screen_size', 'external_dimensions',
            'resolution', 'display_size', 'display_color',
            'built_in_interface', 'weight', 'compatible_software_package',
            # SERVO
            'rated_torque', 'maximum_torque', 'rated_speed', 'maximum_speed',
            'power_supply_capacity', 'power_supply_input', 'rated_voltage',
            'rated_current', 'maximum_current', 'control_method', 'dynamic_brake',
            'encoder_type', 'communication', 'encoder_resolution', 'servo_motor',
            'servo_amplifier',
        ]


class HMIProductForm(BaseProductForm):
    class Meta(BaseProductForm.Meta):
        exclude = [
            # VFD
            'rated_output_power', 'rated_output_current', 'input_voltage',
            'input_frequency', 'output_frequency_range', 'output_voltage', 'dimensions',
            # PLC
            'plc_input', 'plc_output', 'supply_voltage', 'output_type',
            # SERVO
            'rated_torque', 'maximum_torque', 'rated_speed', 'maximum_speed',
            'power_supply_capacity', 'power_supply_input', 'rated_voltage',
            'rated_current', 'maximum_current', 'control_method', 'dynamic_brake',
            'encoder_type', 'communication', 'encoder_resolution', 'servo_motor',
            'servo_amplifier',
        ]


class SERVOProductForm(BaseProductForm):
    class Meta(BaseProductForm.Meta):
        exclude = [
            # VFD
            'rated_output_power', 'rated_output_current', 'input_voltage',
            'input_frequency', 'output_frequency_range', 'output_voltage', 'dimensions',
            # PLC
            'plc_input', 'plc_output', 'supply_voltage', 'output_type',
            # HMI
            'display_device', 'screen_size', 'external_dimensions',
            'resolution', 'display_size', 'display_color',
            'built_in_interface', 'weight', 'compatible_software_package',
        ]


##############################
# Quotation-Related Forms
##############################
class ProductSelectWidget(forms.Select):
    """
    Attaches data-price to each <option> for auto-filling
    the QuotationLine unit_price in JS.
    """
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex=subindex, attrs=attrs)
        if value not in [None, '']:
            try:
                product = self.choices.queryset.get(pk=value)
                option['attrs']['data-price'] = str(product.original_price)
                sys.stderr.write(
                    f"ProductSelectWidget: data-price={product.original_price} for product pk={value}\n"
                )
            except Exception as e:
                sys.stderr.write(f"ProductSelectWidget error pk={value}: {e}\n")
        return option


class QuotationHeaderForm(forms.ModelForm):
    phone_no = forms.CharField(
        required=True,
        label="Phone No",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    customer_name = forms.CharField(
        required=False,
        label="Customer Name",
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.CharField(
        required=False,
        label="Email (Optional)",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    delivery_address = forms.CharField(
        required=False,
        label="Delivery Address (Optional)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,           # Fewer lines
            'style': 'height:50px;'  # Fix the height to ~50px
        })
    )
    subject = forms.CharField(
        required=False,
        label="Subject",
        widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'})
    )

    class Meta:
        model = Quotation
        fields = [
            'customer_name', 'phone_no', 'email',
            'delivery_address', 'subject',
        ]
        widgets = {
            'subject': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class QuotationLineForm(forms.ModelForm):
    # Force discount_percent to always show 2 decimal places, e.g. 25.00
    discount_percent = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        initial=Decimal('25.00'),
        label="Discount (%)"
    )

    # Display SKU as label, and use SKU as the choice label
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        label="SKU",
        widget=ProductSelectWidget(attrs={'class': 'form-select product-select'})
    )

    class Meta:
        model = QuotationLine
        fields = ['product', 'description', 'quantity', 'unit_price', 'discount_percent']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["product"].label_from_instance = lambda obj: obj.sku
        self.fields['quantity'].widget.attrs.update({'class': 'form-control quantity-input'})
        self.fields['unit_price'].widget.attrs.update({'class': 'form-control unit-price-input'})
        self.fields['discount_percent'].widget.attrs.update({'class': 'form-control discount-input'})
        if not self.instance.pk:
            self.fields['discount_percent'].initial = Decimal('25.00')

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get("product")
        unit_price = cleaned_data.get("unit_price")
        if product and (not unit_price or unit_price == 0):
            cleaned_data["unit_price"] = product.original_price
        return cleaned_data


# >>> The key fix: set extra=1 to ensure at least one empty line if no lines exist <<<
QuotationLineFormSet = inlineformset_factory(
    Quotation,
    QuotationLine,
    form=QuotationLineForm,
    extra=1,  # changed from 0 -> ensures 1 blank line if no lines exist
    can_delete=True
)


##############################
# NEW: Order Update Form
##############################
class OrderUpdateForm(forms.ModelForm):
    class Meta:
        model = Quotation
        # Include status and customer information fields
        fields = ['status', 'customer_name', 'phone_no', 'email', 'delivery_address']
