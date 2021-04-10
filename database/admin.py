from django.contrib import admin

from database.models import Job, Subscriber, Result

admin.site.register(Job)
admin.site.register(Result)
admin.site.register(Subscriber)
