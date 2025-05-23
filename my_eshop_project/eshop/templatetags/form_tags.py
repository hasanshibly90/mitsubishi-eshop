from django import template

register = template.Library()

@register.filter(name="add_class")
def add_class(field, css):
    """Renders a form field widget with an extra CSS class."""
    return field.as_widget(attrs={"class": css})
