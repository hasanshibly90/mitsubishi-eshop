from django import template

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    """
    Custom filter that injects a CSS class into a form field widget.
    """
    return field.as_widget(attrs={"class": css})
