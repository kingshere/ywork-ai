from rest_framework import authentication
from rest_framework import exceptions
from django.conf import settings
from django.contrib.auth.models import User
from .models import UserProfile
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from datetime import datetime, timedelta

class GoogleTokenAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header:
            return None

        try:
            # Extract the token
            auth_parts = auth_header.split(' ')
            if len(auth_parts) != 2 or auth_parts[0].lower() != 'bearer':
                return None
            token = auth_parts[1]

            # Find the user profile with this token
            try:
                profile = UserProfile.objects.get(access_token=token)
                
                # Check if token is expired
                if profile.token_expiry < datetime.now():
                    # Try to refresh the token
                    credentials = Credentials(
                        token=profile.access_token,
                        refresh_token=profile.refresh_token,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=settings.GOOGLE_CLIENT_ID,
                        client_secret=settings.GOOGLE_CLIENT_SECRET,
                    )
                    
                    if credentials.expired and credentials.refresh_token:
                        credentials.refresh(Request())
                        profile.access_token = credentials.token
                        profile.token_expiry = datetime.now() + timedelta(seconds=credentials.expires_in)
                        profile.save()
                    else:
                        raise exceptions.AuthenticationFailed('Token expired and could not be refreshed')
                
                return (profile.user, None)
            except UserProfile.DoesNotExist:
                raise exceptions.AuthenticationFailed('Invalid token')
                
        except Exception as e:
            raise exceptions.AuthenticationFailed(f'Authentication failed: {str(e)}')