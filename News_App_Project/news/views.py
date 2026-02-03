"""
Views for News Application

This module contains view functions for:
- Landing page (public)
- User registration (public)
- Article approval workflow (editors only)
- Article listing and detail views
- Newsletter views
- Role-based access control
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Q
from django import forms

from .models import Article, Newsletter, Publisher, CustomUser


# ===== FORMS =====

class ArticleCreateForm(forms.ModelForm):
    """Form for journalists to create articles."""
    
    class Meta:
        model = Article
        fields = ['title', 'content', 'publisher']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter article title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Write your article content here...'
            }),
            'publisher': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        help_texts = {
            'title': 'Enter a compelling title for your article.',
            'content': 'Write the full content of your article.',
            'publisher': 'Optional: Select a publisher if this article is for a specific organization.',
        }


class NewsletterCreateForm(forms.ModelForm):
    """Form for journalists to create newsletters."""
    
    class Meta:
        model = Newsletter
        fields = ['title', 'description', 'articles']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter newsletter title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe this newsletter...'
            }),
            'articles': forms.CheckboxSelectMultiple(),
        }
        help_texts = {
            'title': 'Enter a title for your newsletter.',
            'description': 'Provide a brief description of what this newsletter covers.',
            'articles': 'Select articles to include in this newsletter.',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_journalist:
            # Only show approved articles by this journalist
            self.fields['articles'].queryset = Article.objects.filter(
                author=user,
                approved=True
            )


class UserRegistrationForm(forms.ModelForm):
    """Form for user registration with role selection."""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Password',
        min_length=8,
        help_text='Password must be at least 8 characters'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm Password'
    )
    
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
        help_texts = {
            'username': 'Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.',
            'email': 'Required. A valid email address.',
            'role': 'Choose your role: Reader (view content), Journalist (create content), or Editor (approve content).',
        }
    
    def clean_password_confirm(self):
        """Validate that passwords match."""
        password = self.cleaned_data.get('password')
        password_confirm = self.cleaned_data.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords don't match")
        return password_confirm
    
    def save(self, commit=True):
        """Save user with hashed password."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


# ===== PUBLIC VIEWS =====

def landing(request):
    """
    Display landing page for non-authenticated users.
    Redirect authenticated users to their dashboard.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered landing page template or redirect to dashboard
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'news/landing.html')


def register(request):
    """
    Handle user registration with role selection.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered registration form or redirect to dashboard on success
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                f'Welcome {user.username}! Your account has been created successfully.'
            )
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'news/register.html', {'form': form})


# ===== HELPER FUNCTIONS =====

def is_editor(user):
    """
    Check if user has editor role.
    
    Args:
        user: CustomUser instance
    
    Returns:
        Boolean indicating if user is an editor
    """
    return user.is_authenticated and user.role == CustomUser.EDITOR


def is_journalist(user):
    """
    Check if user has journalist role.
    
    Args:
        user: CustomUser instance
    
    Returns:
        Boolean indicating if user is a journalist
    """
    return user.is_authenticated and user.role == CustomUser.JOURNALIST


def is_editor_or_journalist(user):
    """
    Check if user has editor or journalist role.
    
    Args:
        user: CustomUser instance
    
    Returns:
        Boolean indicating if user is an editor or journalist
    """
    return user.is_authenticated and user.role in [CustomUser.EDITOR, CustomUser.JOURNALIST]


# ===== ARTICLE VIEWS =====

@login_required
def article_list(request):
    """
    Display list of articles based on user's role.
    
    - Readers: See only approved articles
    - Editors: See all articles (for review)
    - Journalists: See their own articles
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with article list
    """
    user = request.user
    
    # Filter articles based on user role
    if user.is_editor:
        # Editors see all articles for review
        articles = Article.objects.all().order_by('-created_at')
        context_title = "All Articles (Editor View)"
    elif user.is_journalist:
        # Journalists see their own articles
        articles = Article.objects.filter(author=user).order_by('-created_at')
        context_title = "My Articles"
    else:  # Reader
        # Readers only see approved articles
        articles = Article.objects.filter(approved=True).order_by('-created_at')
        context_title = "Published Articles"
    
    context = {
        'articles': articles,
        'title': context_title,
        'user_role': user.get_role_display(),
    }
    
    return render(request, 'news/article_list.html', context)


@login_required
def article_detail(request, article_id):
    """
    Display detailed view of a single article.
    
    Args:
        request: HTTP request object
        article_id: ID of the article to display
    
    Returns:
        Rendered template with article details
    
    Raises:
        PermissionDenied: If user doesn't have permission to view the article
    """
    article = get_object_or_404(Article, pk=article_id)
    user = request.user
    
    # Check permissions
    # Readers can only view approved articles
    if user.is_reader and not article.approved:
        raise PermissionDenied("You don't have permission to view this article.")
    
    # Journalists can only view their own unapproved articles or any approved articles
    if user.is_journalist and not article.approved and article.author != user:
        raise PermissionDenied("You don't have permission to view this article.")
    
    context = {
        'article': article,
        'can_approve': user.is_editor and not article.approved,
        'can_edit': user.is_editor or (user.is_journalist and article.author == user),
    }
    
    return render(request, 'news/article_detail.html', context)


# ===== ARTICLE APPROVAL VIEWS (EDITORS ONLY) =====

@login_required
@user_passes_test(is_editor, login_url='/access-denied/')
def pending_articles(request):
    """
    Display list of articles pending approval.
    
    Only accessible by editors.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with pending articles
    """
    # Get all unapproved articles
    articles = Article.objects.filter(approved=False).order_by('-created_at')
    
    context = {
        'articles': articles,
        'title': 'Pending Articles',
    }
    
    return render(request, 'news/pending_articles.html', context)


@login_required
@user_passes_test(is_editor, login_url='/access-denied/')
def approve_article(request, article_id):
    """
    Approve an article (editors only).
    
    This view handles the approval workflow:
    1. Validate user is an editor
    2. Update article approval status
    3. Trigger signals (email + Twitter post)
    4. Redirect with success message
    
    Args:
        request: HTTP request object
        article_id: ID of the article to approve
    
    Returns:
        Redirect to pending articles or article detail
    """
    article = get_object_or_404(Article, pk=article_id)
    
    # Double-check user is an editor (defense in depth)
    if not request.user.is_editor:
        raise PermissionDenied("Only editors can approve articles.")
    
    # Check if article is already approved
    if article.approved:
        messages.warning(request, f"Article '{article.title}' is already approved.")
        return redirect('article_detail', article_id=article.id)
    
    try:
        # Approve the article
        article.approved = True
        article.approved_by = request.user
        article.approved_at = timezone.now()
        article.save()  # This will trigger the post_save signal
        
        messages.success(
            request,
            f"Article '{article.title}' has been approved successfully! "
            f"Notifications have been sent to subscribers."
        )
        
    except Exception as e:
        messages.error(
            request,
            f"Error approving article: {str(e)}"
        )
    
    # Redirect to pending articles list
    return redirect('pending_articles')


@login_required
@user_passes_test(is_editor, login_url='/access-denied/')
def reject_article(request, article_id):
    """
    Reject/delete an article (editors only).
    
    Args:
        request: HTTP request object
        article_id: ID of the article to reject
    
    Returns:
        Redirect to pending articles list
    """
    article = get_object_or_404(Article, pk=article_id)
    
    # Double-check user is an editor
    if not request.user.is_editor:
        raise PermissionDenied("Only editors can reject articles.")
    
    try:
        article_title = article.title
        article.delete()
        messages.success(request, f"Article '{article_title}' has been rejected and deleted.")
    except Exception as e:
        messages.error(request, f"Error rejecting article: {str(e)}")
    
    return redirect('pending_articles')


# ===== NEWSLETTER VIEWS =====

@login_required
def newsletter_list(request):
    """
    Display list of newsletters.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with newsletter list
    """
    newsletters = Newsletter.objects.all().order_by('-created_at')
    
    context = {
        'newsletters': newsletters,
        'title': 'Newsletters',
    }
    
    return render(request, 'news/newsletter_list.html', context)


@login_required
def newsletter_detail(request, newsletter_id):
    """
    Display detailed view of a newsletter.
    
    Args:
        request: HTTP request object
        newsletter_id: ID of the newsletter to display
    
    Returns:
        Rendered template with newsletter details
    """
    newsletter = get_object_or_404(Newsletter, pk=newsletter_id)
    
    # Get only approved articles for readers
    if request.user.is_reader:
        articles = newsletter.get_approved_articles()
    else:
        articles = newsletter.articles.all()
    
    context = {
        'newsletter': newsletter,
        'articles': articles,
    }
    
    return render(request, 'news/newsletter_detail.html', context)


# ===== UTILITY VIEWS =====

def access_denied(request):
    """
    Display access denied page.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered access denied template
    """
    return render(request, 'news/access_denied.html', status=403)


@login_required
def dashboard(request):
    """
    Display user dashboard with role-specific content.
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered dashboard template
    """
    user = request.user
    context = {
        'user': user,
    }
    
    # Add role-specific context
    if user.is_editor:
        context['pending_count'] = Article.objects.filter(approved=False).count()
        context['recent_articles'] = Article.objects.all().order_by('-created_at')[:5]
    elif user.is_journalist:
        context['my_articles'] = Article.objects.filter(author=user).order_by('-created_at')[:5]
        context['my_newsletters'] = Newsletter.objects.filter(author=user).order_by('-created_at')[:5]
    else:  # Reader
        subscriptions = user.get_subscriptions()
        context['subscribed_publishers'] = subscriptions['publishers']
        context['subscribed_journalists'] = subscriptions['journalists']
        context['recent_articles'] = Article.objects.filter(approved=True).order_by('-created_at')[:5]
    
    return render(request, 'news/dashboard.html', context)


# ===== ARTICLE/NEWSLETTER CREATION VIEWS (JOURNALISTS ONLY) =====

@login_required
@user_passes_test(is_journalist, login_url='/access-denied/')
def create_article(request):
    """
    Create a new article (journalists only).
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered article creation form or redirect to article detail on success
    """
    if request.method == 'POST':
        form = ArticleCreateForm(request.POST)
        if form.is_valid():
            article = form.save(commit=False)
            article.author = request.user
            article.approved = False  # Articles need editor approval
            article.save()
            messages.success(
                request,
                f"Article '{article.title}' created successfully! It will be reviewed by an editor."
            )
            return redirect('article_detail', article_id=article.id)
    else:
        form = ArticleCreateForm()
    
    context = {
        'form': form,
        'title': 'Create New Article',
    }
    
    return render(request, 'news/article_form.html', context)


@login_required
@user_passes_test(is_journalist, login_url='/access-denied/')
def create_newsletter(request):
    """
    Create a new newsletter (journalists only).
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered newsletter creation form or redirect to newsletter detail on success
    """
    if request.method == 'POST':
        form = NewsletterCreateForm(request.POST, user=request.user)
        if form.is_valid():
            newsletter = form.save(commit=False)
            newsletter.author = request.user
            newsletter.save()
            form.save_m2m()  # Save many-to-many relationships (articles)
            messages.success(
                request,
                f"Newsletter '{newsletter.title}' created successfully!"
            )
            return redirect('newsletter_detail', newsletter_id=newsletter.id)
    else:
        form = NewsletterCreateForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Create New Newsletter',
    }
    
    return render(request, 'news/newsletter_form.html', context)


# ===== SUBSCRIPTION VIEWS (READERS ONLY) =====

@login_required
def toggle_publisher_subscription(request, publisher_id):
    """
    Toggle subscription to a publisher (readers only).
    
    Args:
        request: HTTP request object
        publisher_id: ID of the publisher
    
    Returns:
        Redirect to previous page with success message
    """
    if not request.user.is_reader:
        messages.error(request, "Only readers can subscribe to publishers.")
        return redirect('dashboard')
    
    publisher = get_object_or_404(Publisher, pk=publisher_id)
    user = request.user
    
    # Toggle subscription
    if publisher in user.subscribed_publishers.all():
        user.subscribed_publishers.remove(publisher)
        messages.success(request, f"Unsubscribed from {publisher.name}")
    else:
        user.subscribed_publishers.add(publisher)
        messages.success(request, f"Subscribed to {publisher.name}")
    
    # Redirect to the previous page or dashboard
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def toggle_journalist_subscription(request, journalist_id):
    """
    Toggle subscription to a journalist (readers only).
    
    Args:
        request: HTTP request object
        journalist_id: ID of the journalist
    
    Returns:
        Redirect to previous page with success message
    """
    if not request.user.is_reader:
        messages.error(request, "Only readers can subscribe to journalists.")
        return redirect('dashboard')
    
    journalist = get_object_or_404(CustomUser, pk=journalist_id, role=CustomUser.JOURNALIST)
    user = request.user
    
    # Toggle subscription
    if journalist in user.subscribed_journalists.all():
        user.subscribed_journalists.remove(journalist)
        messages.success(request, f"Unsubscribed from {journalist.get_full_name() or journalist.username}")
    else:
        user.subscribed_journalists.add(journalist)
        messages.success(request, f"Subscribed to {journalist.get_full_name() or journalist.username}")
    
    # Redirect to the previous page or dashboard
    return redirect(request.META.get('HTTP_REFERER', 'dashboard'))


@login_required
def browse_subscriptions(request):
    """
    Browse available publishers and journalists for subscription (readers only).
    
    Args:
        request: HTTP request object
    
    Returns:
        Rendered template with available subscriptions
    """
    if not request.user.is_reader:
        messages.error(request, "Only readers can access subscription browsing.")
        return redirect('dashboard')
    
    user = request.user
    
    # Get all publishers and journalists
    publishers = Publisher.objects.all().order_by('name')
    journalists = CustomUser.objects.filter(role=CustomUser.JOURNALIST).order_by('username')
    
    # Get user's current subscriptions
    subscribed_publishers = user.subscribed_publishers.all()
    subscribed_journalists = user.subscribed_journalists.all()
    
    context = {
        'publishers': publishers,
        'journalists': journalists,
        'subscribed_publishers': subscribed_publishers,
        'subscribed_journalists': subscribed_journalists,
    }
    
    return render(request, 'news/browse_subscriptions.html', context)

