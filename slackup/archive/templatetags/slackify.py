from django import template
from django.utils.html import format_html
from django.core.exceptions import ObjectDoesNotExist
import re

register = template.Library()

def fix_user(users, matchobj):
    try:
        user = users.get(id=matchobj.group(1))
        return '@{}'.format(user.name)
    except ObjectDoesNotExist:
        return matchobj.group(1)

def fix_channel(channels, matchobj):
    try:
        channel = channels.get(id=matchobj.group(1))
        return '#{}'.format(channel.name)
    except ObjectDoesNotExist:
        return matchobj.group(1)

def fix_links(matchobj):
    link = matchobj.group(1)
    return format_html('<a target="_" href="{}">{}</a>',
                       link, link)

user_re = r'<@(\w+)>'
channel_re = r'<#(\w+)'
link_re = r'<(http[^>]+)>'

@register.simple_tag()
def slackify(format_string, users, channels):
    format_string = re.sub(user_re,
                           lambda id: fix_user(users, id),
                           format_string)
    format_string = re.sub(channel_re,
                           lambda id: fix_channel(channels, id),
                           format_string)
    format_string = re.sub(link_re, fix_links, format_string)
    return format_string
