from django import template

register = template.Library()


@register.filter(name="is_in_group")
def is_in_group(user, group_name):
    if user.is_superuser:
        return True
    return user.groups.filter(name=group_name).exists()


@register.filter(name="not_in_group")
def not_in_group(user, group_name):
    if user.groups.filter(name=group_name).exists():
        return False
    return True
