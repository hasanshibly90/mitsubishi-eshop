from django import template

register = template.Library()

@register.filter
def indian_format(value, decimal_places=2):
    try:
        dp = int(decimal_places)
        num = float(value)
    except (ValueError, TypeError):
        return value

    s = f"{num:.{dp}f}"
    if '.' in s:
        integer, fraction = s.split('.')
    else:
        integer, fraction = s, ''
    
    if len(integer) <= 3:
        return s

    last3 = integer[-3:]
    remaining = integer[:-3]
    groups = []
    while len(remaining) > 2:
        groups.append(remaining[-2:])
        remaining = remaining[:-2]
    if remaining:
        groups.append(remaining)
    groups.reverse()
    formatted_int = ",".join(groups) + "," + last3
    return formatted_int + "." + fraction if fraction else formatted_int
