from django.contrib import admin
from .models import UserProfile, Order

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'google_id')
    search_fields = ('user__username', 'google_id')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'description', 'user__username')