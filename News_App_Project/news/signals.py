"""
Django Signals for News Application

This module contains signal handlers for post-approval actions on articles:
1. Send email notifications to subscribers
2. Post approved articles to Twitter/X

Signals are triggered automatically when articles are approved.
"""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import requests
import logging

from .models import Article, CustomUser

# Set up logging for debugging and error tracking
logger = logging.getLogger(__name__)


@receiver(pre_save, sender=Article)
def track_approval_changes(sender, instance, **kwargs):
    """
    Track when an article's approval status changes.
    
    This signal runs before saving and stores whether the article
    was just approved so we can trigger post-approval actions.
    """
    if instance.pk:  # Only for existing articles
        try:
            old_instance = Article.objects.get(pk=instance.pk)
            # Check if article was just approved
            instance._was_just_approved = (
                not old_instance.approved and instance.approved
            )
        except Article.DoesNotExist:
            instance._was_just_approved = False
    else:
        instance._was_just_approved = False


@receiver(post_save, sender=Article)
def handle_article_approval(sender, instance, created, **kwargs):
    """
    Handle post-approval actions for articles.
    
    When an article is approved:
    1. Update approval timestamp
    2. Send email notifications to subscribers
    3. Post to Twitter/X
    
    Args:
        sender: The model class (Article)
        instance: The actual Article instance
        created: Boolean indicating if this is a new article
        **kwargs: Additional keyword arguments
    """
    # Only proceed if article was just approved
    if not getattr(instance, '_was_just_approved', False):
        return
    
    logger.info(
        f"Article '{instance.title}' was approved. "
        "Triggering post-approval actions..."
    )
    
    # Update approval timestamp if not already set
    if not instance.approved_at:
        instance.approved_at = timezone.now()
        # Use update() to avoid triggering signals again
        Article.objects.filter(pk=instance.pk).update(
            approved_at=instance.approved_at
        )
    
    try:
        # 1. Send email notifications to subscribers
        send_email_to_subscribers(instance)
        
        # 2. Post to Twitter/X
        post_to_twitter(instance)
        
        logger.info(
            f"Successfully completed post-approval actions "
            f"for article '{instance.title}'"
        )
        
    except Exception as e:
        logger.error(
            f"Error in post-approval actions "
            f"for article '{instance.title}': {str(e)}"
        )
        # Don't raise - we don't want to prevent article from being saved


def send_email_to_subscribers(article):
    """
    Send email notification to all subscribers of the article's source.
    
    Sends to:
    - Subscribers of the journalist (if independent article)
    - Subscribers of the publisher (if publisher content)
    
    Args:
        article: The approved Article instance
    
    Raises:
        Exception: If email sending fails
    """
    try:
        # Get subscribers based on article type
        subscribers = get_article_subscribers(article)
        
        if not subscribers:
            logger.info(f"No subscribers found for article '{article.title}'")
            return
        
        # Prepare email content
        subject = f"New Article: {article.title}"
        
        # Get source name for the email
        if article.author:
            source_name = (
                article.author.get_full_name() or article.author.username
            )
            source_type = "journalist"
        else:
            source_name = article.publisher.name
            source_type = "publisher"
        
        message = f"""
Hello,

A new article has been published by {source_name} ({source_type}).

Title: {article.title}

{article.content[:200]}{'...' if len(article.content) > 200 else ''}

---
This is an automated notification from Dispatch.
        """.strip()
        
        # Get subscriber emails
        recipient_emails = [sub.email for sub in subscribers if sub.email]
        
        if not recipient_emails:
            logger.warning(
                f"No valid email addresses found for subscribers "
                f"of article '{article.title}'"
            )
            return
        
        # Send email
        # In development, this will print to console
        # In production, configure SMTP settings in settings.py
        send_mail(
            subject=subject,
            message=message,
            from_email=(
                settings.DEFAULT_FROM_EMAIL
                if hasattr(settings, 'DEFAULT_FROM_EMAIL')
                else 'noreply@newsapp.com'
            ),
            recipient_list=recipient_emails,
            fail_silently=False,
        )
        
        logger.info(f"Sent email notification to {len(recipient_emails)} subscribers for article '{article.title}'")
        
    except Exception as e:
        logger.error(f"Failed to send email for article '{article.title}': {str(e)}")
        raise


def get_article_subscribers(article):
    """
    Get all subscribers for an article based on its source.
    
    Args:
        article: The Article instance
    
    Returns:
        QuerySet of CustomUser instances who are subscribed
    """
    subscribers = CustomUser.objects.none()
    
    try:
        if article.is_independent:
            # Get subscribers of the journalist
            subscribers = article.author.journalist_subscribers.filter(
                role=CustomUser.READER,
                is_active=True
            )
        elif article.is_publisher_content:
            # Get subscribers of the publisher
            subscribers = article.publisher.subscribers.filter(
                role=CustomUser.READER,
                is_active=True
            )
    except Exception as e:
        logger.error(f"Error getting subscribers for article '{article.title}': {str(e)}")
    
    return subscribers


def post_to_twitter(article):
    """
    Post approved article to Twitter/X using the API.
    
    Creates a tweet with:
    - Article title
    - Truncated content (if needed to fit character limit)
    
    Args:
        article: The approved Article instance
    
    Raises:
        Exception: If Twitter API call fails
    """
    try:
        # Check if Twitter credentials are configured
        if not hasattr(settings, 'TWITTER_BEARER_TOKEN') or \
           settings.TWITTER_BEARER_TOKEN == 'your-bearer-token':
            logger.warning("Twitter API credentials not configured. Skipping Twitter post.")
            return
        
        # Prepare tweet content
        # Twitter allows 280 characters
        max_length = 250  # Leave room for URL if needed
        
        # Get source name
        if article.author:
            source_name = article.author.get_full_name() or article.author.username
        else:
            source_name = article.publisher.name
        
        # Create tweet text
        tweet_text = f"{article.title}\n\nBy {source_name}\n\n"
        
        # Add content preview if there's room
        remaining_chars = max_length - len(tweet_text)
        if remaining_chars > 50:
            content_preview = article.content[:remaining_chars - 3] + "..."
            tweet_text += content_preview
        
        # Twitter API v2 endpoint for creating tweets
        url = "https://api.twitter.com/2/tweets"
        
        # Prepare headers and payload
        headers = {
            "Authorization": f"Bearer {settings.TWITTER_BEARER_TOKEN}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "text": tweet_text
        }
        
        # Make POST request to Twitter API
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        # Check response
        if response.status_code == 201:
            logger.info(f"Successfully posted article '{article.title}' to Twitter")
            tweet_data = response.json()
            logger.debug(f"Twitter response: {tweet_data}")
        else:
            logger.error(
                f"Failed to post to Twitter. Status: {response.status_code}, "
                f"Response: {response.text}"
            )
            raise Exception(f"Twitter API returned status {response.status_code}")
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error posting to Twitter for article '{article.title}': {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error posting to Twitter for article '{article.title}': {str(e)}")
        raise
