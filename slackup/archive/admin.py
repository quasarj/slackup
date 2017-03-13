from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Channel)
admin.site.register(SUser)
admin.site.register(Message)
admin.site.register(File)
