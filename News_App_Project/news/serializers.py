"""
Django REST Framework Serializers for News API

This module defines serializers for converting model instances to/from JSON
for the RESTful API endpoints.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Article, Newsletter, Publisher

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser model.
    
    Provides basic user information for API responses.
    """
    
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'role_display']
        read_only_fields = ['id', 'role_display']


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for Publisher model.
    
    Includes basic publisher information and counts.
    """
    
    article_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Publisher
        fields = ['id', 'name', 'description', 'website', 'article_count', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_article_count(self, obj):
        """Get the number of approved articles for this publisher."""
        return obj.articles.filter(approved=True).count()


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Serializer for Article list views.
    
    Provides summary information for article listings.
    """
    
    author_name = serializers.SerializerMethodField()
    publisher_name = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    approved_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'author', 'author_name', 'publisher', 'publisher_name',
            'source', 'approved', 'approved_by', 'approved_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'approved_by', 'approved_at']
    
    def get_author_name(self, obj):
        """Get the author's full name or username."""
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return None
    
    def get_publisher_name(self, obj):
        """Get the publisher's name."""
        return obj.publisher.name if obj.publisher else None
    
    def get_source(self, obj):
        """Get the source of the article (author or publisher)."""
        return str(obj.get_source())
    
    def get_approved_by_name(self, obj):
        """Get the name of the editor who approved the article."""
        if obj.approved_by:
            return obj.approved_by.get_full_name() or obj.approved_by.username
        return None


class ArticleDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Article detail views.
    
    Includes full article content and related information.
    """
    
    author_details = UserSerializer(source='author', read_only=True)
    publisher_details = PublisherSerializer(source='publisher', read_only=True)
    approved_by_details = UserSerializer(source='approved_by', read_only=True)
    source = serializers.SerializerMethodField()
    is_independent = serializers.BooleanField(read_only=True)
    is_publisher_content = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'author', 'author_details',
            'publisher', 'publisher_details', 'source',
            'is_independent', 'is_publisher_content',
            'approved', 'approved_by', 'approved_by_details', 'approved_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'approved_by', 'approved_at', 'created_at', 'updated_at']
    
    def get_source(self, obj):
        """Get the source of the article."""
        return str(obj.get_source())
    
    def validate(self, data):
        """
        Validate that article has either author OR publisher, not both.
        """
        author = data.get('author')
        publisher = data.get('publisher')
        
        # For updates, get current values if not provided
        if self.instance:
            author = author if 'author' in data else self.instance.author
            publisher = publisher if 'publisher' in data else self.instance.publisher
        
        # Validate mutual exclusivity
        if author and publisher:
            raise serializers.ValidationError(
                "Article cannot have both an author and a publisher."
            )
        
        if not author and not publisher:
            raise serializers.ValidationError(
                "Article must have either an author or a publisher."
            )
        
        return data


class ArticleCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating articles.
    
    Used by journalists to create new articles.
    """
    
    class Meta:
        model = Article
        fields = ['title', 'content', 'author', 'publisher']
    
    def validate(self, data):
        """
        Validate article creation.
        
        - Ensure user is creating for themselves or a valid publisher
        - Validate mutual exclusivity of author/publisher
        """
        request = self.context.get('request')
        user = request.user if request else None
        
        author = data.get('author')
        publisher = data.get('publisher')
        
        # Validate mutual exclusivity
        if author and publisher:
            raise serializers.ValidationError(
                "Article cannot have both an author and a publisher."
            )
        
        if not author and not publisher:
            raise serializers.ValidationError(
                "Article must have either an author or a publisher."
            )
        
        # Validate journalist is creating for themselves
        if user and user.is_journalist and author:
            if author != user:
                raise serializers.ValidationError(
                    "Journalists can only create articles for themselves."
                )
        
        return data


class NewsletterSerializer(serializers.ModelSerializer):
    """
    Serializer for Newsletter model.
    
    Includes articles and author information.
    """
    
    author_details = UserSerializer(source='author', read_only=True)
    articles_summary = serializers.SerializerMethodField()
    article_count = serializers.IntegerField(source='get_article_count', read_only=True)
    
    class Meta:
        model = Newsletter
        fields = [
            'id', 'title', 'description', 'author', 'author_details',
            'articles', 'articles_summary', 'article_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_articles_summary(self, obj):
        """Get summary information for articles in the newsletter."""
        # Only show approved articles to readers
        request = self.context.get('request')
        if request and request.user.is_reader:
            articles = obj.get_approved_articles()
        else:
            articles = obj.articles.all()
        
        return ArticleListSerializer(articles, many=True, context=self.context).data


class NewsletterCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating newsletters.
    
    Used by journalists to create new newsletters.
    """
    
    class Meta:
        model = Newsletter
        fields = ['title', 'description', 'author', 'articles']
    
    def validate_author(self, value):
        """
        Validate that the author is a journalist.
        """
        request = self.context.get('request')
        user = request.user if request else None
        
        # Validate journalist is creating for themselves
        if user and user.is_journalist:
            if value != user:
                raise serializers.ValidationError(
                    "Journalists can only create newsletters for themselves."
                )
        
        return value
