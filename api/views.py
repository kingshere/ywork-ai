import os
import json
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import redirect
from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from .models import Order, UserProfile
from .serializers import OrderSerializer, UserProfileSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def google_auth(request):
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return Response({'auth_url': auth_url})

@api_view(['GET'])
@permission_classes([AllowAny])
def google_callback(request):
   
    code = request.GET.get('code')
    if not code:
        return Response({'error': 'Authorization code not found'}, status=status.HTTP_400_BAD_REQUEST)
    
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
            }
        },
        scopes=['https://www.googleapis.com/auth/userinfo.email', 'https://www.googleapis.com/auth/userinfo.profile'],
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )
    
   
    flow.fetch_token(code=code)
    credentials = flow.credentials
  
    service = build('oauth2', 'v2', credentials=credentials)
    user_info = service.userinfo().get().execute()
    
   
    try:
        profile = UserProfile.objects.get(google_id=user_info['id'])
        user = profile.user
       
        profile.access_token = credentials.token
        profile.refresh_token = credentials.refresh_token or profile.refresh_token
        profile.token_expiry = timezone.now() + timezone.timedelta(seconds=credentials.expires_in)
        profile.save()
    except UserProfile.DoesNotExist:
   
        email = user_info.get('email')
        username = email.split('@')[0] if email else user_info.get('id')
        
        
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=email,
            first_name=user_info.get('given_name', ''),
            last_name=user_info.get('family_name', '')
        )
        
        profile = UserProfile.objects.create(
            user=user,
            google_id=user_info['id'],
            access_token=credentials.token,
            refresh_token=credentials.refresh_token or '',
            token_expiry=timezone.now() + timezone.timedelta(seconds=credentials.expires_in)
        )
    
    
    return Response({
        'access_token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'expires_in': credentials.expires_in,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
    })


class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
     
        user = self.request.user
        queryset = Order.objects.filter(user=user)
        
        
        title = self.request.query_params.get('title', None)
        if title is not None:
            queryset = queryset.filter(title__icontains=title)
            
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)