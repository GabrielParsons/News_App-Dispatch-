"""
Comprehensive Unit Tests for News Application API

This test suite covers all requirements:
1. Authentication and authorization per role
2. Article CRUD operations
3. Subscription-based filtering
4. Newsletter operations
5. Approval workflow
6. Signal functionality (email and Twitter posting)
7. Both successful and failed request scenarios

Run with: python manage.py test news.test_comprehensive
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from news.models import Article, Newsletter, Publisher, CustomUser

User = get_user_model()


# ========== MODEL VALIDATION TESTS ==========

class ModelValidationTestCase(TestCase):
    """Test model validation rules and constraints."""
    
    def setUp(self):
        """Set up test users and publishers."""
        self.reader = User.objects.create_user(
            username='reader_test',
            password='testpass123',
            email='reader@test.com',
            role=CustomUser.READER
        )
        self.journalist = User.objects.create_user(
            username='journalist_test',
            password='testpass123',
            email='journalist@test.com',
            role=CustomUser.JOURNALIST
        )
        self.editor = User.objects.create_user(
            username='editor_test',
            password='testpass123',
            email='editor@test.com',
            role=CustomUser.EDITOR
        )
        self.publisher = Publisher.objects.create(
            name='Test Publisher',
            description='A test publisher'
        )
    
    def test_article_cannot_have_both_author_and_publisher(self):
        """Test that article validation prevents both author and publisher."""
        article = Article(
            title='Test Article',
            content='Test content',
            author=self.journalist,
            publisher=self.publisher
        )
        with self.assertRaises(Exception):
            article.save()
    
    def test_article_must_have_author_or_publisher(self):
        """Test that article must have either author or publisher."""
        article = Article(
            title='Test Article',
            content='Test content'
        )
        with self.assertRaises(Exception):
            article.save()
    
    def test_independent_article_creation(self):
        """Test creating independent article with journalist author."""
        article = Article.objects.create(
            title='Independent Article',
            content='By a journalist',
            author=self.journalist
        )
        self.assertTrue(article.is_independent)
        self.assertFalse(article.is_publisher_content)
        self.assertEqual(article.get_source(), self.journalist)
    
    def test_publisher_article_creation(self):
        """Test creating publisher article."""
        article = Article.objects.create(
            title='Publisher Article',
            content='By a publisher',
            publisher=self.publisher
        )
        self.assertFalse(article.is_independent)
        self.assertTrue(article.is_publisher_content)
        self.assertEqual(article.get_source(), self.publisher)
    
    def test_user_role_properties(self):
        """Test user role convenience properties."""
        self.assertTrue(self.reader.is_reader)
        self.assertFalse(self.reader.is_editor)
        self.assertFalse(self.reader.is_journalist)
        
        self.assertTrue(self.editor.is_editor)
        self.assertFalse(self.editor.is_reader)
        
        self.assertTrue(self.journalist.is_journalist)
        self.assertFalse(self.journalist.is_reader)
    
    def test_reader_subscriptions(self):
        """Test reader subscription functionality."""
        another_journalist = User.objects.create_user(
            username='j2',
            password='pass',
            role=CustomUser.JOURNALIST
        )
        
        self.reader.subscribed_journalists.add(self.journalist, another_journalist)
        self.reader.subscribed_publishers.add(self.publisher)
        
        subscriptions = self.reader.get_subscriptions()
        self.assertEqual(subscriptions['journalists'].count(), 2)
        self.assertEqual(subscriptions['publishers'].count(), 1)
    
    def test_newsletter_creation(self):
        """Test newsletter model."""
        newsletter = Newsletter.objects.create(
            title='Test Newsletter',
            description='Test description',
            author=self.journalist
        )
        
        article1 = Article.objects.create(
            title='Article 1',
            content='Content 1',
            author=self.journalist,
            approved=True
        )
        article2 = Article.objects.create(
            title='Article 2',
            content='Content 2',
            author=self.journalist,
            approved=False
        )
        
        newsletter.articles.add(article1, article2)
        
        self.assertEqual(newsletter.get_article_count(), 2)
        self.assertEqual(newsletter.get_approved_articles().count(), 1)


# ========== API AUTHENTICATION TESTS ==========

class APIAuthenticationTestCase(APITestCase):
    """Test JWT authentication for API."""
    
    def setUp(self):
        """Create test user."""
        self.user = User.objects.create_user(
            username='api_user',
            password='testpass123',
            email='api@test.com',
            role=CustomUser.READER
        )
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_jwt_token_obtain_success(self):
        """Test successful JWT token generation."""
        response = self.client.post('/api/token/', {
            'username': 'api_user',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_jwt_token_obtain_failure(self):
        """Test JWT token generation with wrong credentials."""
        response = self.client.post('/api/token/', {
            'username': 'api_user',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_jwt_token_refresh(self):
        """Test JWT token refresh functionality."""
        # Get initial tokens
        response = self.client.post('/api/token/', {
            'username': 'api_user',
            'password': 'testpass123'
        })
        refresh_token = response.data['refresh']
        
        # Refresh token
        response = self.client.post('/api/token/refresh/', {
            'refresh': refresh_token
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


# ========== ARTICLE API TESTS ==========

class ArticleAPITestCase(APITestCase):
    """Test Article API endpoints with role-based permissions."""
    
    def setUp(self):
        """Set up test data."""
        self.reader = User.objects.create_user(
            username='reader', password='pass', role=CustomUser.READER
        )
        self.journalist = User.objects.create_user(
            username='journalist', password='pass', role=CustomUser.JOURNALIST
        )
        self.editor = User.objects.create_user(
            username='editor', password='pass', role=CustomUser.EDITOR
        )
        
        # Create test articles
        self.approved_article = Article.objects.create(
            title='Approved Article',
            content='This is approved content',
            author=self.journalist,
            approved=True
        )
        self.pending_article = Article.objects.create(
            title='Pending Article',
            content='This is pending content',
            author=self.journalist,
            approved=False
        )
    
    def _authenticate(self, user):
        """Helper method to authenticate a user and set token."""
        response = self.client.post('/api/token/', {
            'username': user.username,
            'password': 'pass'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    
    def test_reader_sees_only_approved_articles(self):
        """Test that readers can only see approved articles."""
        self._authenticate(self.reader)
        response = self.client.get('/api/articles/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        article_ids = [a['id'] for a in response.data['results']]
        self.assertIn(self.approved_article.id, article_ids)
        self.assertNotIn(self.pending_article.id, article_ids)
    
    def test_journalist_sees_all_articles(self):
        """Test that journalists can see all articles."""
        self._authenticate(self.journalist)
        response = self.client.get('/api/articles/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        article_ids = [a['id'] for a in response.data['results']]
        self.assertIn(self.approved_article.id, article_ids)
        self.assertIn(self.pending_article.id, article_ids)
    
    def test_journalist_can_create_article(self):
        """Test that journalists can create articles."""
        self._authenticate(self.journalist)
        response = self.client.post('/api/articles/', {
            'title': 'New Article',
            'content': 'New content',
            'author': self.journalist.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Article.objects.filter(title='New Article').count(), 1)
    
    def test_reader_cannot_create_article(self):
        """Test that readers cannot create articles."""
        self._authenticate(self.reader)
        response = self.client.post('/api/articles/', {
            'title': 'New Article',
            'content': 'New content'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_journalist_can_update_own_article(self):
        """Test that journalists can update their own articles."""
        self._authenticate(self.journalist)
        response = self.client.patch(
            f'/api/articles/{self.pending_article.id}/',
            {'title': 'Updated Title'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.pending_article.refresh_from_db()
        self.assertEqual(self.pending_article.title, 'Updated Title')
    
    def test_editor_can_update_any_article(self):
        """Test that editors can update any article."""
        self._authenticate(self.editor)
        response = self.client.patch(
            f'/api/articles/{self.pending_article.id}/',
            {'content': 'Editor updated content'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_reader_cannot_update_article(self):
        """Test that readers cannot update articles."""
        self._authenticate(self.reader)
        response = self.client.patch(
            f'/api/articles/{self.approved_article.id}/',
            {'title': 'Hacked Title'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_editor_can_delete_article(self):
        """Test that editors can delete articles."""
        self._authenticate(self.editor)
        article_to_delete = Article.objects.create(
            title='Delete Me',
            content='Content',
            author=self.journalist
        )
        
        response = self.client.delete(f'/api/articles/{article_to_delete.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Article.objects.filter(id=article_to_delete.id).exists())
    
    def test_reader_cannot_delete_article(self):
        """Test that readers cannot delete articles."""
        self._authenticate(self.reader)
        response = self.client.delete(f'/api/articles/{self.approved_article.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Article.objects.filter(id=self.approved_article.id).exists())


# ========== ARTICLE APPROVAL TESTS ==========

class ArticleApprovalTestCase(APITestCase):
    """Test article approval workflow."""
    
    def setUp(self):
        """Set up test data."""
        self.editor = User.objects.create_user(
            username='editor',
            password='pass',
            email='editor@test.com',
            role=CustomUser.EDITOR
        )
        self.journalist = User.objects.create_user(
            username='journalist',
            password='pass',
            email='journalist@test.com',
            role=CustomUser.JOURNALIST
        )
        self.reader = User.objects.create_user(
            username='reader',
            password='pass',
            email='reader@test.com',
            role=CustomUser.READER
        )
        
        self.article = Article.objects.create(
            title='Pending Article',
            content='Content to be approved',
            author=self.journalist,
            approved=False
        )
    
    def _authenticate(self, user):
        """Helper to authenticate."""
        response = self.client.post('/api/token/', {
            'username': user.username,
            'password': 'pass'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
    
    def test_editor_can_approve_article(self):
        """Test that editors can approve articles."""
        self._authenticate(self.editor)
        
        with patch('news.signals.send_email_to_subscribers'), \
             patch('news.signals.post_to_twitter'):
            response = self.client.post(f'/api/articles/{self.article.id}/approve/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.article.refresh_from_db()
        self.assertTrue(self.article.approved)
        self.assertEqual(self.article.approved_by, self.editor)
        self.assertIsNotNone(self.article.approved_at)
    
    def test_journalist_cannot_approve_article(self):
        """Test that journalists cannot approve articles."""
        self._authenticate(self.journalist)
        response = self.client.post(f'/api/articles/{self.article.id}/approve/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.article.refresh_from_db()
        self.assertFalse(self.article.approved)
    
    def test_reader_cannot_approve_article(self):
        """Test that readers cannot approve articles."""
        self._authenticate(self.reader)
        response = self.client.post(f'/api/articles/{self.article.id}/approve/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ========== SUBSCRIPTION FILTER TESTS ==========

class SubscriptionFilterTestCase(APITestCase):
    """Test subscription-based article filtering."""
    
    def setUp(self):
        """Set up test data."""
        self.reader = User.objects.create_user(
            username='reader',
            password='pass',
            role=CustomUser.READER
        )
        self.journalist1 = User.objects.create_user(
            username='j1',
            password='pass',
            role=CustomUser.JOURNALIST
        )
        self.journalist2 = User.objects.create_user(
            username='j2',
            password='pass',
            role=CustomUser.JOURNALIST
        )
        self.publisher = Publisher.objects.create(name='Test Publisher')
        
        # Subscribe reader to journalist1 and publisher
        self.reader.subscribed_journalists.add(self.journalist1)
        self.reader.subscribed_publishers.add(self.publisher)
        
        # Create articles
        self.article1 = Article.objects.create(
            title='From J1',
            content='Content',
            author=self.journalist1,
            approved=True
        )
        self.article2 = Article.objects.create(
            title='From J2',
            content='Content',
            author=self.journalist2,
            approved=True
        )
        self.article3 = Article.objects.create(
            title='From Publisher',
            content='Content',
            publisher=self.publisher,
            approved=True
        )
    
    def test_subscribed_endpoint_filters_correctly(self):
        """Test that /api/articles/subscribed/ returns only subscribed content."""
        # Authenticate
        response = self.client.post('/api/token/', {
            'username': 'reader',
            'password': 'pass'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        
        # Get subscribed articles
        response = self.client.get('/api/articles/subscribed/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        article_ids = [a['id'] for a in response.data['results']]
        
        # Should include articles from j1 and publisher
        self.assertIn(self.article1.id, article_ids)
        self.assertIn(self.article3.id, article_ids)
        
        # Should NOT include article from j2
        self.assertNotIn(self.article2.id, article_ids)


# ========== NEWSLETTER API TESTS ==========

class NewsletterAPITestCase(APITestCase):
    """Test Newsletter API endpoints."""
    
    def setUp(self):
        """Set up test data."""
        self.journalist = User.objects.create_user(
            username='journalist',
            password='pass',
            role=CustomUser.JOURNALIST
        )
        self.editor = User.objects.create_user(
            username='editor',
            password='pass',
            role=CustomUser.EDITOR
        )
        self.reader = User.objects.create_user(
            username='reader',
            password='pass',
            role=CustomUser.READER
        )
        
        self.newsletter = Newsletter.objects.create(
            title='Test Newsletter',
            description='Test description',
            author=self.journalist
        )
    
    def _authenticate(self, user):
        """Helper to authenticate."""
        response = self.client.post('/api/token/', {
            'username': user.username,
            'password': 'pass'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
    
    def test_journalist_can_create_newsletter(self):
        """Test that journalists can create newsletters."""
        self._authenticate(self.journalist)
        response = self.client.post('/api/newsletters/', {
            'title': 'New Newsletter',
            'description': 'Description',
            'author': self.journalist.id
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_reader_cannot_create_newsletter(self):
        """Test that readers cannot create newsletters."""
        self._authenticate(self.reader)
        response = self.client.post('/api/newsletters/', {
            'title': 'New Newsletter',
            'description': 'Description'
        })
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_editor_can_update_newsletter(self):
        """Test that editors can update newsletters."""
        self._authenticate(self.editor)
        response = self.client.patch(
            f'/api/newsletters/{self.newsletter.id}/',
            {'title': 'Updated Title'}
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_reader_can_view_newsletters(self):
        """Test that readers can view newsletters."""
        self._authenticate(self.reader)
        response = self.client.get('/api/newsletters/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ========== SIGNAL TESTS ==========

class SignalTestCase(TestCase):
    """Test signal functionality for article approval."""
    
    def setUp(self):
        """Set up test data."""
        self.editor = User.objects.create_user(
            username='editor',
            password='pass',
            email='editor@test.com',
            role=CustomUser.EDITOR
        )
        self.journalist = User.objects.create_user(
            username='journalist',
            password='pass',
            email='journalist@test.com',
            role=CustomUser.JOURNALIST
        )
        self.reader = User.objects.create_user(
            username='reader',
            password='pass',
            email='reader@test.com',
            role=CustomUser.READER
        )
        
        # Subscribe reader to journalist
        self.reader.subscribed_journalists.add(self.journalist)
    
    def test_approval_triggers_email(self):
        """Test that approving article sends email to subscribers."""
        article = Article.objects.create(
            title='Test Article',
            content='Test content',
            author=self.journalist
        )
        
        # Mock Twitter posting to avoid external calls
        with patch('news.signals.post_to_twitter'):
            article.approved = True
            article.approved_by = self.editor
            article.save()
        
        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Test Article', mail.outbox[0].subject)
        self.assertIn('reader@test.com', mail.outbox[0].to)
    
    def test_approval_calls_twitter_post(self):
        """Test that approving article calls Twitter posting."""
        article = Article.objects.create(
            title='Test Article',
            content='Test content',
            author=self.journalist
        )
        
        with patch('news.signals.post_to_twitter') as mock_twitter:
            article.approved = True
            article.approved_by = self.editor
            article.save()
            
            # Verify Twitter function was called
            mock_twitter.assert_called_once_with(article)
    
    def test_no_signal_on_create(self):
        """Test that signals don't fire on article creation."""
        with patch('news.signals.send_email_to_subscribers') as mock_email:
            Article.objects.create(
                title='New Article',
                content='Content',
                author=self.journalist,
                approved=False
            )
            
            # Email should not be sent for new unapproved articles
            mock_email.assert_not_called()
    
    def test_no_signal_on_content_update(self):
        """Test that signals don't fire when updating content without approval."""
        article = Article.objects.create(
            title='Article',
            content='Original content',
            author=self.journalist,
            approved=False
        )
        
        with patch('news.signals.send_email_to_subscribers') as mock_email:
            article.content = 'Updated content'
            article.save()
            
            mock_email.assert_not_called()


# ========== ERROR HANDLING TESTS ==========

class ErrorHandlingTestCase(APITestCase):
    """Test error handling and edge cases."""
    
    def setUp(self):
        """Set up test data."""
        self.journalist = User.objects.create_user(
            username='journalist',
            password='pass',
            role=CustomUser.JOURNALIST
        )
    
    def test_invalid_article_id(self):
        """Test accessing non-existent article."""
        response = self.client.post('/api/token/', {
            'username': 'journalist',
            'password': 'pass'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        
        response = self.client.get('/api/articles/99999/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = self.client.post('/api/token/', {
            'username': 'journalist',
            'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_missing_required_fields(self):
        """Test creating article without required fields."""
        response = self.client.post('/api/token/', {
            'username': 'journalist',
            'password': 'pass'
        })
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        
        response = self.client.post('/api/articles/', {
            'title': 'Incomplete'
            # Missing content and author
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
