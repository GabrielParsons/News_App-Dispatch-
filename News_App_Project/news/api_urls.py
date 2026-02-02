"""
API URL Configuration for News Application

Maps API endpoints to ViewSets using Django REST Framework routers.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ArticleViewSet, NewsletterViewSet, PublisherViewSet, UserViewSet

# Create a router and register our viewsets
router = DefaultRouter()
router.register(r'articles', ArticleViewSet, basename='article')
router.register(r'newsletters', NewsletterViewSet, basename='newsletter')
router.register(r'publishers', PublisherViewSet, basename='publisher')
router.register(r'users', UserViewSet, basename='user')

# The API URLs are now determined automatically by the router
urlpatterns = [
    path('', include(router.urls)),
]
