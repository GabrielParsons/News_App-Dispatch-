"""
Comprehensive Unit Tests for News Application API

Tests cover: authentication, authorization, CRUD operations, subscriptions, and signals.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from unittest.mock import patch
from django.core import mail

from news.models import Article, Newsletter, Publisher, CustomUser

User = get_user_model()


class ModelTestCase(TestCase):
    """Test model validation and methods."""
    
    def setUp(self):
        self.reader = User.objects.create_user(username='reader', password='pass', role=CustomUser.READER)
        self.journalist = User.objects.create_user(username='journalist', password='pass', role=CustomUser.JOURNALIST)
        self.publisher = Publisher.objects.create(name='Test Publisher')
    
    def test_article_validation_both_author_and_publisher(self):
        """Article cannot have both author and publisher."""
        article = Article(title='Test', content='Content', author=self.journalist, publisher=self.publisher)
        with self.assertRaises(Exception):
            article.save()
    
    def test_article_independent_property(self):
        """Test article independent property."""
        article = Article.objects.create(title='Test', content='Content', author=self.journalist)
        self.assertTrue(article.is_independent)
        self.assertFalse(article.is_publisher_content)


class APIAuthenticationTestCase(APITestCase):
    """Test API authentication."""
    
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass', role=CustomUser.READER)
    
    def test_api_requires_authentication(self):
        """API endpoints require authentication."""
        response = self.client.get('/api/articles/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_jwt_token_obtain(self):
        """Test obtaining JWT token."""
        response = self.client.post('/api/token/', {'username': 'user', 'password': 'pass'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class ArticleAPITestCase(APITestCase):
    """Test Article API endpoints."""
    
    def setUp(self):
        self.reader = User.objects.create_user(username='reader', password='pass', role=CustomUser.READER)
        self.journalist = User.objects.create_user(username='journalist', password='pass', role=CustomUser.JOURNALIST)
        self.editor = User.objects.create_user(username='editor', password='pass', role=CustomUser.EDITOR)
        
        self.approved_article = Article.objects.create(
            title='Approved', content='Content', author=self.journalist, approved=True
        )
        self.pending_article = Article.objects.create(
            title='Pending', content='Content', author=self.journalist, approved=False
        )
    
    def _auth(self, user):
        """Helper to authenticate."""
        response = self.client.post('/api/token/', {'username': user.username, 'password': 'pass'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
    
    def test_reader_sees_only_approved(self):
        """Readers see only approved articles."""
        self._auth(self.reader)
        response = self.client.get('/api/articles/')
        ids = [a['id'] for a in response.data['results']]
        self.assertIn(self.approved_article.id, ids)
        self.assertNotIn(self.pending_article.id, ids)
    
    def test_journalist_can_create(self):
        """Journalists can create articles."""
        self._auth(self.journalist)
        response = self.client.post('/api/articles/', {
            'title': 'New', 'content': 'Content', 'author': self.journalist.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_reader_cannot_create(self):
        """Readers cannot create articles."""
        self._auth(self.reader)
        response = self.client.post('/api/articles/', {'title': 'New', 'content': 'Content'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_editor_can_approve(self):
        """Editors can approve articles."""
        self._auth(self.editor)
        with patch('news.signals.send_email_to_subscribers'), patch('news.signals.post_to_twitter'):
            response = self.client.post(f'/api/articles/{self.pending_article.id}/approve/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.pending_article.refresh_from_db()
            self.assertTrue(self.pending_article.approved)


class SubscriptionFilterTestCase(APITestCase):
    """Test subscription-based filtering."""
    
    def setUp(self):
        self.reader = User.objects.create_user(username='reader', password='pass', role=CustomUser.READER)
        self.journalist1 = User.objects.create_user(username='j1', password='pass', role=CustomUser.JOURNALIST)
        self.journalist2 = User.objects.create_user(username='j2', password='pass', role=CustomUser.JOURNALIST)
        
        self.reader.subscribed_journalists.add(self.journalist1)
        
        self.article1 = Article.objects.create(title='A1', content='C', author=self.journalist1, approved=True)
        self.article2 = Article.objects.create(title='A2', content='C', author=self.journalist2, approved=True)
    
    def test_subscribed_endpoint(self):
        """Subscribed endpoint returns only subscribed articles."""
        response = self.client.post('/api/token/', {'username': 'reader', 'password': 'pass'})
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')
        
        response = self.client.get('/api/articles/subscribed/')
        ids = [a['id'] for a in response.data['results']]
        self.assertIn(self.article1.id, ids)
        self.assertNotIn(self.article2.id, ids)


class SignalTestCase(TestCase):
    """Test signal functionality."""
    
    def setUp(self):
        self.editor = User.objects.create_user(username='editor', password='pass', email='e@test.com', role=CustomUser.EDITOR)
        self.journalist = User.objects.create_user(username='j', password='pass', email='j@test.com', role=CustomUser.JOURNALIST)
        self.reader = User.objects.create_user(username='r', password='pass', email='r@test.com', role=CustomUser.READER)
        self.reader.subscribed_journalists.add(self.journalist)
    
    def test_approval_sends_email(self):
        """Approving article sends email to subscribers."""
        article = Article.objects.create(title='Test', content='Content', author=self.journalist)
        
        with patch('news.signals.post_to_twitter'):
            article.approved = True
            article.approved_by = self.editor
            article.save()
        
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('Test', mail.outbox[0].subject)

