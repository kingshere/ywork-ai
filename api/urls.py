from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('auth/google/', views.google_auth, name='google_auth'),
    path('auth/google/callback/', views.google_callback, name='google_callback'),
]