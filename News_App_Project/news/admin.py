"""
Django Admin Configuration for News Application

Registers all models with customized admin interfaces for better management.
Restricts admin access to superusers only.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import AdminSite

from .models import CustomUser, Publisher, Article, Newsletter


class RestrictedAdminSite(AdminSite):
    """
    Custom admin site that only allows superusers to access.
    Regular users (even editors and journalists) cannot access the admin panel.
    """
    
    def has_permission(self, request):
        """
        Only allow superusers to access the admin site.
        """
        return request.user.is_active and request.user.is_superuser


# Create a custom admin site instance
admin_site = RestrictedAdminSite(name='restricted_admin')


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Custom admin interface for CustomUser model.
    """
    
    # Fields to display in the list view
    list_display = ['username', 'email', 'role', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['role', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    # Organize fields in the edit form
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Role'), {'fields': ('role',)}),
        (_('Subscriptions (Reader only)'), {
            'fields': ('subscribed_publishers', 'subscribed_journalists'),
            'description': 'These fields should only be used for users with Reader role.'
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields for adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
    
    filter_horizontal = ('groups', 'user_permissions', 'subscribed_publishers', 'subscribed_journalists')


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """
    Admin interface for Publisher model.
    """
    
    list_display = ['name', 'website', 'created_at', 'get_article_count']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    filter_horizontal = ['editors', 'journalists']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'website')
        }),
        (_('Staff'), {
            'fields': ('editors', 'journalists'),
            'description': 'Editors and journalists associated with this publisher.'
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def get_article_count(self, obj):
        """Get the number of articles for this publisher."""
        return obj.articles.count()
    get_article_count.short_description = 'Article Count'


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Admin interface for Article model with approval workflow.
    """
    
    list_display = ['title', 'get_source', 'approved', 'approved_by', 'created_at']
    list_filter = ['approved', 'created_at', 'updated_at']
    search_fields = ['title', 'content', 'author__username', 'publisher__name']
    readonly_fields = ['created_at', 'updated_at', 'approved_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'content')
        }),
        (_('Source'), {
            'fields': ('author', 'publisher'),
            'description': 'Set either author (for independent articles) OR publisher (for publisher content), not both.'
        }),
        (_('Approval'), {
            'fields': ('approved', 'approved_by', 'approved_at'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def get_source(self, obj):
        """Get the source of the article."""
        return obj.get_source()
    get_source.short_description = 'Source'


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """
    Admin interface for Newsletter model.
    """
    
    list_display = ['title', 'author', 'get_article_count', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['title', 'description', 'author__username']
    filter_horizontal = ['articles']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'author')
        }),
        (_('Articles'), {
            'fields': ('articles',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )
    
    def get_article_count(self, obj):
        """Get the number of articles in this newsletter."""
        return obj.get_article_count()
    get_article_count.short_description = 'Article Count'

