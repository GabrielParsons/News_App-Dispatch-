"""
Custom Permissions for News API

This module defines custom permission classes for role-based access control
in the REST API.
"""

from rest_framework import permissions
from .models import CustomUser


class IsEditor(permissions.BasePermission):
    """
    Permission class to check if user has Editor role.
    """
    
    def has_permission(self, request, view):
        """Check if user is an editor."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.EDITOR
        )


class IsJournalist(permissions.BasePermission):
    """
    Permission class to check if user has Journalist role.
    """
    
    def has_permission(self, request, view):
        """Check if user is a journalist."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.JOURNALIST
        )


class IsReader(permissions.BasePermission):
    """
    Permission class to check if user has Reader role.
    """
    
    def has_permission(self, request, view):
        """Check if user is a reader."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.READER
        )


class IsEditorOrJournalist(permissions.BasePermission):
    """
    Permission class to check if user has Editor or Journalist role.
    """
    
    def has_permission(self, request, view):
        """Check if user is an editor or journalist."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role in [CustomUser.EDITOR, CustomUser.JOURNALIST]
        )


class IsJournalistOrReadOnly(permissions.BasePermission):
    """
    Permission class that allows:
    - Journalists to create articles
    - Anyone authenticated to read
    """
    
    def has_permission(self, request, view):
        """Check permissions based on request method."""
        # Read permissions are allowed to any authenticated user
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Write permissions only for journalists
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.JOURNALIST
        )


class CanModifyArticle(permissions.BasePermission):
    """
    Permission class for article modification.
    
    - Editors can modify any article
    - Journalists can only modify their own articles
    - Readers cannot modify articles
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can modify the article."""
        # Read permissions for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        
        # Editors can modify any article
        if request.user.role == CustomUser.EDITOR:
            return True
        
        # Journalists can only modify their own articles
        if request.user.role == CustomUser.JOURNALIST:
            return obj.author == request.user
        
        # Readers cannot modify
        return False


class CanApproveArticle(permissions.BasePermission):
    """
    Permission class for article approval.
    
    Only editors can approve articles.
    """
    
    def has_permission(self, request, view):
        """Check if user can approve articles."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.EDITOR
        )
    
    def has_object_permission(self, request, view, obj):
        """Check if user can approve this specific article."""
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == CustomUser.EDITOR
        )


class CanViewArticle(permissions.BasePermission):
    """
    Permission class for viewing articles.
    
    - Readers can only view approved articles
    - Editors can view all articles
    - Journalists can view their own articles (approved or not) and all approved articles
    """
    
    def has_object_permission(self, request, view, obj):
        """Check if user can view this article."""
        user = request.user
        
        # Not authenticated - no access
        if not user or not user.is_authenticated:
            return False
        
        # Editors can view all articles
        if user.role == CustomUser.EDITOR:
            return True
        
        # Approved articles visible to all authenticated users
        if obj.approved:
            return True
        
        # Journalists can view their own unapproved articles
        if user.role == CustomUser.JOURNALIST and obj.author == user:
            return True
        
        # Readers cannot view unapproved articles
        return False
