"""
URL Configuration for News Application

Maps URLs to views for landing page, registration, article approval, listing, and newsletters.
"""

from django.urls import path
from . import views

urlpatterns = [
    # Public pages
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    
    # Dashboard (authenticated users)
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Article URLs
    path('articles/', views.article_list, name='article_list'),
    path('articles/<int:article_id>/', views.article_detail, name='article_detail'),
    path('articles/create/', views.create_article, name='create_article'),
    
    # Article Approval URLs (Editors only)
    path('pending/', views.pending_articles, name='pending_articles'),
    path('articles/<int:article_id>/approve/', views.approve_article, name='approve_article'),
    path('articles/<int:article_id>/reject/', views.reject_article, name='reject_article'),
    
    # Newsletter URLs
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/<int:newsletter_id>/', views.newsletter_detail, name='newsletter_detail'),
    path('newsletters/create/', views.create_newsletter, name='create_newsletter'),
    
    # Subscription URLs (Readers only)
    path('subscriptions/', views.browse_subscriptions, name='browse_subscriptions'),
    path('subscribe/publisher/<int:publisher_id>/', views.toggle_publisher_subscription, name='toggle_publisher_subscription'),
    path('subscribe/journalist/<int:journalist_id>/', views.toggle_journalist_subscription, name='toggle_journalist_subscription'),
    
    # Utility URLs
    path('access-denied/', views.access_denied, name='access_denied'),
]
