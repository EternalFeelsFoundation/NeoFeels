from django.contrib import admin

# Register your models here.

from posts.models import *

class BanInline(admin.TabularInline):
	model = Ban

class PostAdmin(admin.ModelAdmin):
	date_hierarchy = 'time'
	list_display = ('time', 'body', 'ipaddr')
	inlines = [BanInline]

admin.site.register(Post, PostAdmin)
admin.site.register(Tag)
admin.site.register(Ban)
admin.site.register(Log)
