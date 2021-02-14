from django import template

register = template.Library()


@register.filter(name="is_allowed_to")
def is_allowed_to(user, group_name):
    return user.groups.filter(name=group_name).exists()
