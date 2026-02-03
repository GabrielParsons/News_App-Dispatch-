"""
Create Sample Data for Testing

This script creates sample users, publishers, articles, and newsletters
for testing the application.

Usage:
    python manage.py shell < create_sample_data.py
"""

from django.contrib.auth import get_user_model
from news.models import Publisher, Article, Newsletter

User = get_user_model()

print("Creating sample data...")

# Create users
print("\nCreating users...")
reader1, _ = User.objects.get_or_create(
    username='reader1',
    defaults={
        'email': 'reader1@example.com',
        'role': 'reader',
        'first_name': 'Alice',
        'last_name': 'Reader'
    }
)
reader1.set_password('password123')
reader1.save()
print(f"✓ Created reader: {reader1.username}")

journalist1, _ = User.objects.get_or_create(
    username='journalist1',
    defaults={
        'email': 'journalist1@example.com',
        'role': 'journalist',
        'first_name': 'Bob',
        'last_name': 'Writer'
    }
)
journalist1.set_password('password123')
journalist1.save()
print(f"✓ Created journalist: {journalist1.username}")

journalist2, _ = User.objects.get_or_create(
    username='journalist2',
    defaults={
        'email': 'journalist2@example.com',
        'role': 'journalist',
        'first_name': 'Carol',
        'last_name': 'Scribe'
    }
)
journalist2.set_password('password123')
journalist2.save()
print(f"✓ Created journalist: {journalist2.username}")

editor1, _ = User.objects.get_or_create(
    username='editor1',
    defaults={
        'email': 'editor1@example.com',
        'role': 'editor',
        'first_name': 'David',
        'last_name': 'Editor'
    }
)
editor1.set_password('password123')
editor1.save()
print(f"✓ Created editor: {editor1.username}")

# Create publishers
print("\nCreating publishers...")
publisher1, _ = Publisher.objects.get_or_create(
    name='Tech News Daily',
    defaults={
        'description': 'Your source for technology news',
        'website': 'https://technewsdaily.example.com'
    }
)
publisher1.journalists.add(journalist1)
print(f"✓ Created publisher: {publisher1.name}")

publisher2, _ = Publisher.objects.get_or_create(
    name='World Report',
    defaults={
        'description': 'Global news coverage',
        'website': 'https://worldreport.example.com'
    }
)
publisher2.journalists.add(journalist2)
print(f"✓ Created publisher: {publisher2.name}")

# Subscribe reader to journalist and publisher
reader1.subscribed_journalists.add(journalist1)
reader1.subscribed_publishers.add(publisher1)
print(f"✓ Subscribed {reader1.username} to {journalist1.username} and {publisher1.name}")

# Create articles
print("\nCreating articles...")

# Independent journalist article (approved)
article1, _ = Article.objects.get_or_create(
    title='AI Breakthrough in Machine Learning',
    defaults={
        'content': '''Researchers have announced a major breakthrough in machine learning 
        algorithms that could revolutionize the field. The new approach demonstrates 
        unprecedented accuracy in pattern recognition tasks...''',
        'author': journalist1,
        'approved': True,
        'approved_by': editor1
    }
)
print(f"✓ Created article: {article1.title}")

# Pending journalist article
article2, _ = Article.objects.get_or_create(
    title='Future of Quantum Computing',
    defaults={
        'content': '''Quantum computing is poised to transform computational science. 
        Recent developments suggest we may see practical applications sooner than expected...''',
        'author': journalist1,
        'approved': False
    }
)
print(f"✓ Created pending article: {article2.title}")

# Publisher article (approved)
article3, _ = Article.objects.get_or_create(
    title='Global Markets Rally on Economic News',
    defaults={
        'content': '''Stock markets around the world saw significant gains today following 
        positive economic indicators. Analysts are optimistic about the outlook...''',
        'publisher': publisher2,
        'approved': True,
        'approved_by': editor1
    }
)
print(f"✓ Created article: {article3.title}")

# Another independent article
article4, _ = Article.objects.get_or_create(
    title='Climate Change: New Study Reveals Trends',
    defaults={
        'content': '''A comprehensive new study on climate change has revealed worrying 
        trends in global temperature rise. Scientists are calling for immediate action...''',
        'author': journalist2,
        'approved': True,
        'approved_by': editor1
    }
)
print(f"✓ Created article: {article4.title}")

# Create newsletters
print("\nCreating newsletters...")
newsletter1, _ = Newsletter.objects.get_or_create(
    title='Weekly Tech Roundup',
    defaults={
        'description': 'The most important technology news of the week',
        'author': journalist1
    }
)
newsletter1.articles.add(article1, article3)
print(f"✓ Created newsletter: {newsletter1.title}")

newsletter2, _ = Newsletter.objects.get_or_create(
    title='Science & Environment Digest',
    defaults={
        'description': 'Latest developments in science and environmental news',
        'author': journalist2
    }
)
newsletter2.articles.add(article4)
print(f"✓ Created newsletter: {newsletter2.title}")

print("\n" + "="*50)
print("Sample data created successfully!")
print("="*50)
print("\nLogin credentials (password for all: password123):")
print(f"  Reader:     {reader1.username}")
print(f"  Journalist: {journalist1.username}")
print(f"  Journalist: {journalist2.username}")
print(f"  Editor:     {editor1.username}")
print("\nYou can now:")
print("1. Login to admin: http://localhost:8000/admin/")
print("2. Test the API with JWT tokens")
print("3. Test the web interface")
