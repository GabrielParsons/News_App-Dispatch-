"""
Management command to set up user groups and permissions.

This command creates three groups (Reader, Editor, Journalist) and assigns
appropriate permissions to each group based on their roles.

Usage:
    python manage.py setup_groups
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from news.models import Article, Newsletter, Publisher


class Command(BaseCommand):
    """
    Django management command to create and configure user groups.
    """
    
    help = (
        'Sets up user groups (Reader, Editor, Journalist) '
        'with appropriate permissions'
    )

    def handle(self, *args, **kwargs):
        """
        Main method that executes when the command is run.
        Creates groups and assigns permissions based on role requirements.
        """
        self.stdout.write(
            self.style.SUCCESS('Setting up user groups and permissions...')
        )
        
        try:
            # Create groups
            reader_group, created = Group.objects.get_or_create(name='Reader')
            if created:
                self.stdout.write(self.style.SUCCESS('Created Reader group'))
            else:
                self.stdout.write('Reader group already exists')
            
            editor_group, created = Group.objects.get_or_create(name='Editor')
            if created:
                self.stdout.write(self.style.SUCCESS('Created Editor group'))
            else:
                self.stdout.write('Editor group already exists')
            
            journalist_group, created = Group.objects.get_or_create(
                name='Journalist'
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS('Created Journalist group')
                )
            else:
                self.stdout.write('Journalist group already exists')
            
            # Get content types for our models
            article_ct = ContentType.objects.get_for_model(Article)
            newsletter_ct = ContentType.objects.get_for_model(Newsletter)
            publisher_ct = ContentType.objects.get_for_model(Publisher)
            
            # Clear existing permissions from all groups
            reader_group.permissions.clear()
            editor_group.permissions.clear()
            journalist_group.permissions.clear()
            
            # ===== READER PERMISSIONS =====
            # Readers can only VIEW articles and newsletters
            self.stdout.write('\nSetting up Reader permissions...')
            
            reader_permissions = [
                Permission.objects.get(
                    codename='view_article', content_type=article_ct
                ),
                Permission.objects.get(
                    codename='view_newsletter', content_type=newsletter_ct
                ),
                Permission.objects.get(
                    codename='view_publisher', content_type=publisher_ct
                ),
            ]
            
            reader_group.permissions.set(reader_permissions)
            msg = (
                f'  - Assigned {len(reader_permissions)} permissions '
                'to Reader group'
            )
            self.stdout.write(self.style.SUCCESS(msg))
            for perm in reader_permissions:
                self.stdout.write(f'    • {perm.name}')
            
            # ===== EDITOR PERMISSIONS =====
            # Editors can VIEW, UPDATE, and DELETE articles/newsletters
            # (but not create - that's for journalists)
            self.stdout.write('\nSetting up Editor permissions...')
            
            editor_permissions = [
                # Article permissions
                Permission.objects.get(
                    codename='view_article', content_type=article_ct
                ),
                Permission.objects.get(
                    codename='change_article', content_type=article_ct
                ),
                Permission.objects.get(
                    codename='delete_article', content_type=article_ct
                ),
                
                # Newsletter permissions
                Permission.objects.get(
                    codename='view_newsletter', content_type=newsletter_ct
                ),
                Permission.objects.get(
                    codename='change_newsletter', content_type=newsletter_ct
                ),
                Permission.objects.get(
                    codename='delete_newsletter', content_type=newsletter_ct
                ),
                
                # Publisher permissions (view only)
                Permission.objects.get(
                    codename='view_publisher', content_type=publisher_ct
                ),
            ]
            
            editor_group.permissions.set(editor_permissions)
            msg = (
                f'  - Assigned {len(editor_permissions)} permissions '
                'to Editor group'
            )
            self.stdout.write(self.style.SUCCESS(msg))
            for perm in editor_permissions:
                self.stdout.write(f'    • {perm.name}')
            
            # ===== JOURNALIST PERMISSIONS =====
            # Journalists can CREATE, VIEW, UPDATE, DELETE articles/newsletters
            self.stdout.write('\nSetting up Journalist permissions...')
            
            journalist_permissions = [
                # Article permissions (full CRUD)
                Permission.objects.get(
                    codename='add_article', content_type=article_ct
                ),
                Permission.objects.get(
                    codename='view_article', content_type=article_ct
                ),
                Permission.objects.get(
                    codename='change_article', content_type=article_ct
                ),
                Permission.objects.get(
                    codename='delete_article', content_type=article_ct
                ),
                
                # Newsletter permissions (full CRUD)
                Permission.objects.get(
                    codename='add_newsletter', content_type=newsletter_ct
                ),
                Permission.objects.get(
                    codename='view_newsletter', content_type=newsletter_ct
                ),
                Permission.objects.get(
                    codename='change_newsletter', content_type=newsletter_ct
                ),
                Permission.objects.get(
                    codename='delete_newsletter', content_type=newsletter_ct
                ),
                
                # Publisher permissions (view only)
                Permission.objects.get(
                    codename='view_publisher', content_type=publisher_ct
                ),
            ]
            
            journalist_group.permissions.set(journalist_permissions)
            msg = (
                f'  - Assigned {len(journalist_permissions)} permissions '
                'to Journalist group'
            )
            self.stdout.write(self.style.SUCCESS(msg))
            for perm in journalist_permissions:
                self.stdout.write(f'    • {perm.name}')
            
            # Success message
            self.stdout.write(self.style.SUCCESS(
                '\n✓ Successfully set up all groups and permissions!'
            ))
            self.stdout.write(self.style.SUCCESS(
                '\nGroup summary:'
            ))
            self.stdout.write(
                '  - Reader: Can view articles, newsletters, and publishers'
            )
            self.stdout.write(
                '  - Editor: Can view, update, and delete '
                'articles and newsletters'
            )
            self.stdout.write(
                '  - Journalist: Can create, view, update, and delete '
                'articles and newsletters'
            )
            
        except Exception as e:
            error_msg = f'Error setting up groups: {str(e)}'
            self.stdout.write(self.style.ERROR(error_msg))
            raise
