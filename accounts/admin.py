from django.contrib import admin
from .models import CustomUser

@admin.action(description='Approve selected users')
def approve_users(modeladmin, request, queryset):
    queryset.update(is_approved=True)

class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'name', 'surname', 'role', 'is_approved')
    list_filter = ('is_approved', 'role')
    actions = [approve_users]

admin.site.register(CustomUser, CustomUserAdmin)

