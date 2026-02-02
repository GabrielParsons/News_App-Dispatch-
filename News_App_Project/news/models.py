"""
News Application Models

This module contains all database models for the news application including:
- CustomUser: Role-based user model with Reader, Editor, and Journalist roles
- Publisher: Organization that publishes articles
- Article: News articles with approval workflow
- Newsletter: Curated collection of articles
"""

from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """
    Custom user model with role-based functionality.
    
    Supports three roles:
    - READER: Can view articles and newsletters, has subscriptions
    - EDITOR: Can review, approve, update, and delete articles/newsletters
    - JOURNALIST: Can create, view, update, and delete articles/newsletters
    """
    
    # Role choices
    READER = 'reader'
    EDITOR = 'editor'
    JOURNALIST = 'journalist'
    
    ROLE_CHOICES = [
        (READER, 'Reader'),
        (EDITOR, 'Editor'),
        (JOURNALIST, 'Journalist'),
    ]
    
    # Common fields for all users
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=READER,
        help_text=_("User's role in the system")
    )
    
    # Fields for Reader role
    # Readers can subscribe to publishers to receive their content
    subscribed_publishers = models.ManyToManyField(
        'Publisher',
        related_name='subscribers',
        blank=True,
        help_text=_("Publishers this reader is subscribed to")
    )
    
    # Readers can subscribe to individual journalists
    subscribed_journalists = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='journalist_subscribers',
        blank=True,
        limit_choices_to={'role': JOURNALIST},
        help_text=_("Journalists this reader is subscribed to")
    )
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        """
        Override save to automatically assign users to appropriate groups
        based on their role and handle field validation.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Assign user to appropriate group based on role
        if is_new or 'role' in kwargs.get('update_fields', []):
            self._assign_to_group()
    
    def _assign_to_group(self):
        """Assign user to the appropriate group based on their role."""
        # Remove user from all role-based groups
        self.groups.filter(name__in=['Reader', 'Editor', 'Journalist']).delete()
        
        # Add user to the appropriate group
        group_name = self.get_role_display()
        try:
            group = Group.objects.get(name=group_name)
            self.groups.add(group)
        except Group.DoesNotExist:
            # Group will be created by management command
            pass
    
    def clean(self):
        """
        Validate that role-specific fields are only used appropriately.
        Journalists should not have reader subscriptions.
        """
        super().clean()
        
        # Validate that journalists don't have reader-specific data
        if self.role == self.JOURNALIST:
            if self.pk:  # Only check if user exists
                if self.subscribed_publishers.exists() or self.subscribed_journalists.exists():
                    raise ValidationError(
                        _("Journalists cannot have reader subscriptions.")
                    )
    
    def get_authored_articles(self):
        """Get all articles authored by this user (for journalists)."""
        if self.role == self.JOURNALIST:
            return self.authored_articles.all()
        return []
    
    def get_authored_newsletters(self):
        """Get all newsletters authored by this user (for journalists)."""
        if self.role == self.JOURNALIST:
            return self.authored_newsletters.all()
        return []
    
    def get_subscriptions(self):
        """Get all subscriptions for this user (for readers)."""
        if self.role == self.READER:
            return {
                'publishers': self.subscribed_publishers.all(),
                'journalists': self.subscribed_journalists.all()
            }
        return {'publishers': [], 'journalists': []}
    
    @property
    def is_reader(self):
        """Check if user has Reader role."""
        return self.role == self.READER
    
    @property
    def is_editor(self):
        """Check if user has Editor role."""
        return self.role == self.EDITOR
    
    @property
    def is_journalist(self):
        """Check if user has Journalist role."""
        return self.role == self.JOURNALIST


class Publisher(models.Model):
    """
    Publisher model representing organizations that publish articles.
    
    Publishers can have multiple editors and journalists working for them.
    """
    
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text=_("Publisher organization name")
    )
    
    description = models.TextField(
        blank=True,
        help_text=_("Description of the publisher")
    )
    
    website = models.URLField(
        blank=True,
        help_text=_("Publisher's website URL")
    )
    
    # Publisher can have multiple editors
    editors = models.ManyToManyField(
        CustomUser,
        related_name='publisher_editors',
        limit_choices_to={'role': CustomUser.EDITOR},
        blank=True,
        help_text=_("Editors working for this publisher")
    )
    
    # Publisher can have multiple journalists
    journalists = models.ManyToManyField(
        CustomUser,
        related_name='publisher_journalists',
        limit_choices_to={'role': CustomUser.JOURNALIST},
        blank=True,
        help_text=_("Journalists working for this publisher")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the publisher was created")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the publisher was last updated")
    )
    
    class Meta:
        verbose_name = _('Publisher')
        verbose_name_plural = _('Publishers')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def get_all_articles(self):
        """Get all articles published by this publisher."""
        return self.articles.all()
    
    def get_approved_articles(self):
        """Get all approved articles published by this publisher."""
        return self.articles.filter(approved=True)


class Article(models.Model):
    """
    Article model representing news articles.
    
    Articles can be:
    - Independent: Created by a journalist (author field set)
    - Publisher content: Created for a publisher (publisher field set)
    
    Articles must be approved by an editor before being published.
    """
    
    title = models.CharField(
        max_length=300,
        help_text=_("Article title")
    )
    
    content = models.TextField(
        help_text=_("Article content/body")
    )
    
    # Author is the journalist who wrote the article (for independent articles)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='authored_articles',
        limit_choices_to={'role': CustomUser.JOURNALIST},
        null=True,
        blank=True,
        help_text=_("Journalist author (for independent articles)")
    )
    
    # Publisher is set for publisher-owned content
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name='articles',
        null=True,
        blank=True,
        help_text=_("Publisher (for publisher content)")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the article was created")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the article was last updated")
    )
    
    # Approval workflow
    approved = models.BooleanField(
        default=False,
        help_text=_("Whether the article has been approved for publishing")
    )
    
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        related_name='approved_articles',
        limit_choices_to={'role': CustomUser.EDITOR},
        null=True,
        blank=True,
        help_text=_("Editor who approved the article")
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text=_("When the article was approved")
    )
    
    class Meta:
        verbose_name = _('Article')
        verbose_name_plural = _('Articles')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['approved']),
        ]
    
    def __str__(self):
        return self.title
    
    def clean(self):
        """
        Validate that article has either an author OR a publisher, but not both.
        This ensures proper normalization.
        """
        super().clean()
        
        # Article must have either author or publisher, but not both
        if self.author and self.publisher:
            raise ValidationError(
                _("Article cannot have both an author and a publisher. "
                  "Use author for independent articles or publisher for publisher content.")
            )
        
        if not self.author and not self.publisher:
            raise ValidationError(
                _("Article must have either an author (journalist) or a publisher.")
            )
    
    def save(self, *args, **kwargs):
        """Override save to run validation."""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def get_source(self):
        """Get the source of the article (author or publisher)."""
        if self.author:
            return self.author
        return self.publisher
    
    @property
    def is_independent(self):
        """Check if this is an independent article (has author)."""
        return self.author is not None
    
    @property
    def is_publisher_content(self):
        """Check if this is publisher content."""
        return self.publisher is not None


class Newsletter(models.Model):
    """
    Newsletter model representing curated collections of articles.
    
    Newsletters are created by journalists and can contain multiple articles.
    They can be viewed by readers and edited by journalists and editors.
    """
    
    title = models.CharField(
        max_length=300,
        help_text=_("Newsletter title")
    )
    
    description = models.TextField(
        help_text=_("Newsletter description")
    )
    
    # Author is the journalist who created the newsletter
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='authored_newsletters',
        limit_choices_to={'role': CustomUser.JOURNALIST},
        help_text=_("Journalist who created this newsletter")
    )
    
    # Many-to-many relationship with articles
    articles = models.ManyToManyField(
        Article,
        related_name='newsletters',
        blank=True,
        help_text=_("Articles included in this newsletter")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text=_("When the newsletter was created")
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text=_("When the newsletter was last updated")
    )
    
    class Meta:
        verbose_name = _('Newsletter')
        verbose_name_plural = _('Newsletters')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.title
    
    def get_article_count(self):
        """Get the number of articles in this newsletter."""
        return self.articles.count()
    
    def get_approved_articles(self):
        """Get only approved articles in this newsletter."""
        return self.articles.filter(approved=True)
