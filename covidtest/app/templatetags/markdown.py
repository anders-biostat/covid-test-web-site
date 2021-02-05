from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()

@register.filter(name="markdown")
def render_markdown(mdtext):
    return mark_safe(markdown.markdown(mdtext))
