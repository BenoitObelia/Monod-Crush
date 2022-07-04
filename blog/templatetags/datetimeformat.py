from datetime import timedelta

from django import template
from django.contrib.humanize.templatetags.humanize import naturalday, naturaltime
from django.utils.datetime_safe import datetime
from django.utils.timezone import now

register = template.Library()


# noinspection SpellCheckingInspection
@register.filter
def naturaltimeordate(value: datetime) -> str:
    """
    For date and time values show how many seconds, minutes, or hours ago
    compared to current timestamp return representing string. if value is
    """
    if now() - value < timedelta(days=1):
        return naturaltime(value)
    else:
        return f"le {naturalday(value)}"
