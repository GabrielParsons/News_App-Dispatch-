"""
Django REST Framework Views for News API

This module contains ViewSets for the RESTful API endpoints with
role-based access control and subscription filtering.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.utils import timezone

from .models import Article, Newsletter, Publisher, CustomUser
from .serializers import (
    ArticleListSerializer,
    ArticleDetailSerializer,
    ArticleCreateSerializer,
    NewsletterSerializer,
    NewsletterCreateSerializer,
    PublisherSerializer,
    UserSerializer
)
from .permissions import (
    IsJournalistOrReadOnly,
    CanModifyArticle,
    CanApproveArticle,
    CanViewArticle,
    IsEditorOrJournalist,
    IsEditor,
    IsJournalist
)


class ArticleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Article CRUD operations.
    
    Endpoints:
    - GET /api/articles/ - List all approved articles (or filtered by subscriptions)
    - GET /api/articles/<id>/ - Retrieve single article
    - POST /api/articles/ - Create article (journalists only)
    - PUT /api/articles/<id>/ - Update article (editors/journalists)
    - DELETE /api/articles/<id>/ - Delete article (editors/journalists)
    - GET /api/articles/subscribed/ - Get articles from subscribed sources
    - POST /api/articles/<id>/approve/ - Approve article (editors only)
    """
    
    queryset = Article.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'author__username', 'publisher__name']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """
        Return appropriate serializer based on action.
        """
        if self.action == 'create':
            return ArticleCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return ArticleDetailSerializer
        return ArticleListSerializer
    
    def get_queryset(self):
        """
        Filter queryset based on user role and permissions.
        
        - Readers: Only approved articles
        - Editors: All articles
        - Journalists: Their own articles + all approved articles
        """
        user = self.request.user
        queryset = Article.objects.all()
        
        if user.role == CustomUser.READER:
            # Readers only see approved articles
            queryset = queryset.filter(approved=True)
        elif user.role == CustomUser.JOURNALIST:
            # Journalists see their own articles + approved articles
            queryset = queryset.filter(
                Q(approved=True) | Q(author=user)
            )
        # Editors see all articles (no filtering)
        
        return queryset.order_by('-created_at')
    
    def get_permissions(self):
        """
        Set permissions based on action.
        """
        if self.action == 'create':
            # Only journalists can create
            return [IsAuthenticated(), IsJournalist()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Editors and journalists can modify
            return [IsAuthenticated(), CanModifyArticle()]
        elif self.action == 'retrieve':
            # Custom permission for viewing
            return [IsAuthenticated(), CanViewArticle()]
        elif self.action == 'approve':
            # Only editors can approve
            return [IsAuthenticated(), CanApproveArticle()]
        
        # Default: authenticated users can list
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """
        Handle article creation.
        
        Automatically set the author to the current user if they're a journalist.
        """
        user = self.request.user
        
        # If user is journalist and no author specified, set to current user
        if user.role == CustomUser.JOURNALIST:
            if 'author' not in serializer.validated_data:
                serializer.save(author=user)
            else:
                serializer.save()
        else:
            serializer.save()
    
    @action(detail=False, methods=['get'], url_path='subscribed')
    def subscribed(self, request):
        """
        Get articles from subscribed publishers and journalists.
        
        This endpoint returns only articles from sources the user is subscribed to.
        Only available to readers.
        
        GET /api/articles/subscribed/
        """
        user = request.user
        
        # Only readers have subscriptions
        if user.role != CustomUser.READER:
            return Response(
                {'detail': 'Only readers have subscriptions.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get subscribed publishers and journalists
        subscribed_publishers = user.subscribed_publishers.all()
        subscribed_journalists = user.subscribed_journalists.all()
        
        # Filter approved articles from subscribed sources
        articles = Article.objects.filter(
            approved=True
        ).filter(
            Q(publisher__in=subscribed_publishers) |
            Q(author__in=subscribed_journalists)
        ).order_by('-created_at')
        
        # Paginate results
        page = self.paginate_queryset(articles)
        if page is not None:
            serializer = ArticleListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = ArticleListSerializer(articles, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        """
        Approve an article (editors only).
        
        POST /api/articles/<id>/approve/
        
        This triggers the signals that send emails and post to Twitter/X.
        """
        article = self.get_object()
        
        # Check if already approved
        if article.approved:
            return Response(
                {'detail': 'Article is already approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Approve the article
            article.approved = True
            article.approved_by = request.user
            article.approved_at = timezone.now()
            article.save()  # This triggers the post_save signal
            
            serializer = ArticleDetailSerializer(article, context={'request': request})
            return Response({
                'detail': 'Article approved successfully. Notifications sent to subscribers.',
                'article': serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'detail': f'Error approving article: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NewsletterViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Newsletter CRUD operations.
    
    Endpoints:
    - GET /api/newsletters/ - List all newsletters
    - GET /api/newsletters/<id>/ - Retrieve single newsletter
    - POST /api/newsletters/ - Create newsletter (journalists only)
    - PUT /api/newsletters/<id>/ - Update newsletter (editors/journalists)
    - DELETE /api/newsletters/<id>/ - Delete newsletter (editors/journalists)
    """
    
    queryset = Newsletter.objects.all()
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'author__username']
    ordering_fields = ['created_at', 'updated_at', 'title']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == 'create':
            return NewsletterCreateSerializer
        return NewsletterSerializer
    
    def get_permissions(self):
        """Set permissions based on action."""
        if self.action == 'create':
            # Only journalists can create
            return [IsAuthenticated(), IsJournalist()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            # Editors and journalists can modify
            return [IsAuthenticated(), IsEditorOrJournalist()]
        
        # Anyone authenticated can list/retrieve
        return [IsAuthenticated()]
    
    def perform_create(self, serializer):
        """
        Handle newsletter creation.
        
        Automatically set the author to the current user if they're a journalist.
        """
        user = self.request.user
        
        if user.role == CustomUser.JOURNALIST:
            if 'author' not in serializer.validated_data:
                serializer.save(author=user)
            else:
                serializer.save()
        else:
            serializer.save()


class PublisherViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Publisher (read-only).
    
    Endpoints:
    - GET /api/publishers/ - List all publishers
    - GET /api/publishers/<id>/ - Retrieve single publisher
    """
    
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for User (read-only).
    
    Endpoints:
    - GET /api/users/ - List all users
    - GET /api/users/<id>/ - Retrieve single user
    - GET /api/users/me/ - Get current user details
    """
    
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter]
    search_fields = ['username', 'email', 'first_name', 'last_name']
    
    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        """
        Get current user details.
        
        GET /api/users/me/
        """
        serializer = UserSerializer(request.user, context={'request': request})
        return Response(serializer.data)
