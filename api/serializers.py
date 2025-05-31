from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Order, UserProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'google_id']

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'title', 'description', 'user', 'created_at', 'updated_at']
        read_only_fields = ['user', 'created_at', 'updated_at']