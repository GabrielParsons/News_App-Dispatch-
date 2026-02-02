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
    
    # Article Approval URLs (Editors only)
    path('pending/', views.pending_articles, name='pending_articles'),
    path('articles/<int:article_id>/approve/', views.approve_article, name='approve_article'),
    path('articles/<int:article_id>/reject/', views.reject_article, name='reject_article'),
    
    # Newsletter URLs
    path('newsletters/', views.newsletter_list, name='newsletter_list'),
    path('newsletters/<int:newsletter_id>/', views.newsletter_detail, name='newsletter_detail'),
    
    # Utility URLs
    path('access-denied/', views.access_denied, name='access_denied'),
]
