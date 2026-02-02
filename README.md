[README.md](https://github.com/user-attachments/files/25026467/README.md)
# Dispatch - Django News Application

> **Note**: The application is internally named "news" in the Django codebase (app directory, database tables, imports). "Dispatch" is the user-facing brand name used throughout the UI.

A professional, modern Django news application with role-based access control, article approval workflow, RESTful API, and elegant Bootstrap 5 UI.

## ✨ Features

### User Interface
- 🎨 **Professional Bootstrap 5 Design**: Modern, responsive UI with elegant typography using Playfair Display and Lora fonts
- 📱 **Mobile-First Responsive**: Fully responsive design that works seamlessly on all devices
- 🎯 **Intuitive Navigation**: Clean, icon-based navigation with role-specific menu items
- 💫 **Smooth Animations**: Card hover effects and button transitions for enhanced UX
- 🌈 **Custom Color Scheme**: Professional dark blue gradient theme with accent colors

### User Roles
- **Reader**: Can view approved articles and newsletters, subscribe to publishers and journalists
- **Journalist**: Can create, view, update, and delete their own articles and newsletters
- **Editor**: Can review, approve, update, and delete all articles and newsletters

### Core Functionality
- ✅ Custom user model with role-based permissions
- ✅ Article approval workflow with editor review
- ✅ Subscription system (readers can subscribe to publishers/journalists)
- ✅ Automated email notifications when articles are approved
- ✅ Twitter/X integration for posting approved articles
- ✅ RESTful API with JWT authentication
- ✅ Comprehensive unit tests
- ✅ MariaDB database support
- ✅ Bootstrap 5 with custom styling
- ✅ Bootstrap Icons integration

## 🎨 UI/UX Design

### Design System
- **Primary Color**: Deep navy (#1a1a2e)
- **Secondary Color**: Dark blue (#16213e)
- **Accent Color**: Rich blue (#0f3460)
- **Highlight Color**: Vibrant red (#e94560)
- **Typography**: 
  - Headings: Playfair Display (elegant serif)
  - Body: Lora (readable serif)
- **Components**: Custom cards with shadow effects, rounded buttons, and modern badges

### Key UI Features
- Gradient navigation bar with icon-based menu
- Card-based layout with hover animations
- Role-specific dashboards with tailored content
- Icon-enhanced buttons and badges
- Professional page headers with gradients
- Clean, spacious layouts with proper whitespace

## Database Design

The application uses a normalized database schema with the following models:

### CustomUser
- Role-based user model (Reader, Editor, Journalist)
- Reader-specific fields: `subscribed_publishers`, `subscribed_journalists`
- Journalist-specific relationships: `authored_articles`, `authored_newsletters`

### Publisher
- Represents publishing organizations
- Has many-to-many relationships with editors and journalists

### Article
- Either has an `author` (journalist) OR `publisher` (mutual exclusivity enforced)
- Includes approval workflow: `approved`, `approved_by`, `approved_at`
- Cannot have both author and publisher (validation enforced)

### Newsletter
- Created by journalists
- Can contain multiple articles (many-to-many)

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure MariaDB

Create a MariaDB database and user:

```sql
CREATE DATABASE news_app_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'news_user'@'localhost' IDENTIFIED BY 'news_password';
GRANT ALL PRIVILEGES ON news_app_db.* TO 'news_user'@'localhost';
FLUSH PRIVILEGES;
```

Update `news_project/settings.py` with your database credentials if different.

### 3. Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Set Up Groups and Permissions

```bash
python manage.py setup_groups
```

This creates three groups (Reader, Editor, Journalist) with appropriate permissions.

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

When creating the superuser, set their role to Editor in the admin panel.

### 6. Run Development Server

```bash
python manage.py runserver
```

Access the application at: `http://localhost:8000`

## API Endpoints

### Authentication

```
POST /api/token/                 - Obtain JWT token
POST /api/token/refresh/          - Refresh JWT token
```

### Articles

```
GET    /api/articles/             - List all approved articles (or user-specific)
POST   /api/articles/             - Create article (journalists only)
GET    /api/articles/<id>/        - Retrieve single article
PUT    /api/articles/<id>/        - Update article (editors/journalists)
DELETE /api/articles/<id>/        - Delete article (editors/journalists)
GET    /api/articles/subscribed/  - Get articles from subscribed sources (readers)
POST   /api/articles/<id>/approve/ - Approve article (editors only)
```

### Newsletters

```
GET    /api/newsletters/          - List all newsletters
POST   /api/newsletters/          - Create newsletter (journalists only)
GET    /api/newsletters/<id>/     - Retrieve single newsletter
PUT    /api/newsletters/<id>/     - Update newsletter (editors/journalists)
DELETE /api/newsletters/<id>/     - Delete newsletter (editors/journalists)
```

### Publishers

```
GET    /api/publishers/           - List all publishers
GET    /api/publishers/<id>/      - Retrieve single publisher
```

### Users

```
GET    /api/users/                - List all users
GET    /api/users/<id>/           - Retrieve single user
GET    /api/users/me/             - Get current user details
```

## API Usage Examples

### Obtain JWT Token

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "journalist1", "password": "yourpassword"}'
```

### Create Article (as Journalist)

```bash
curl -X POST http://localhost:8000/api/articles/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Breaking News",
    "content": "This is the article content...",
    "author": 2
  }'
```

### Approve Article (as Editor)

```bash
curl -X POST http://localhost:8000/api/articles/1/approve/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Get Subscribed Articles (as Reader)

```bash
curl -X GET http://localhost:8000/api/articles/subscribed/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Web Interface

### Features

The web interface features a **professional Bootstrap 5 design** with:

- **Responsive Grid Layout**: Articles and newsletters displayed in responsive card grids
- **Role-Specific Dashboards**: Customized views for Readers, Journalists, and Editors
- **Icon-Enhanced Navigation**: Bootstrap Icons throughout the interface
- **Smooth Animations**: Card hover effects and button transitions
- **Professional Typography**: Elegant Playfair Display headings with Lora body text
- **Modern Color Scheme**: Dark blue gradients with vibrant accent colors

### URLs

- `/` - Dashboard (role-specific with personalized content)
- `/articles/` - Browse articles in responsive card layout
- `/articles/<id>/` - Full article view with elegant typography
- `/pending/` - Pending articles for approval (editors only)
- `/newsletters/` - Browse newsletters in card grid
- `/newsletters/<id>/` - Newsletter detail with included articles
- `/admin/` - Django admin interface

### Design Highlights

- **Navigation**: Gradient navbar with icon-based menu and role badge
- **Cards**: Custom shadow effects with hover animations
- **Buttons**: Rounded, gradient-filled buttons with smooth transitions
- **Badges**: Modern, rounded badges for status indicators
- **Page Headers**: Full-width gradient headers with large typography
- **Responsive**: Mobile-first design that adapts to all screen sizes

## Signal-Based Automation

When an article is approved, the following actions occur automatically:

1. **Email Notification**: Sends email to all subscribers of the article's source (journalist or publisher)
2. **Twitter/X Post**: Posts the article to Twitter/X using the configured API credentials

### Configure Email (Production)

Update `news_project/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

### Configure Twitter/X API

Update `news_project/settings.py` with your Twitter API credentials:

```python
TWITTER_API_KEY = 'your-api-key'
TWITTER_API_SECRET = 'your-api-secret'
TWITTER_ACCESS_TOKEN = 'your-access-token'
TWITTER_ACCESS_TOKEN_SECRET = 'your-access-token-secret'
TWITTER_BEARER_TOKEN = 'your-bearer-token'
```

## Running Tests

Run the comprehensive test suite:

```bash
python manage.py test news
```

Tests cover:
- Model validation and business logic
- API authentication and authorization
- Role-based access control
- CRUD operations for all roles
- Subscription-based filtering
- Signal functionality (mocked)

## Project Structure

```
News_App_Project/
├── manage.py
├── requirements.txt
├── setup.sh                  # Database setup automation
├── create_sample_data.py     # Sample data generator
├── API_TESTING_GUIDE.md      # Comprehensive API testing guide
├── news_project/
│   ├── settings.py          # Project settings (DB, REST framework, JWT)
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py
└── news/
    ├── models.py            # CustomUser, Article, Publisher, Newsletter
    ├── admin.py             # Admin interface configuration
    ├── views.py             # Web views for article approval
    ├── urls.py              # Web URL patterns
    ├── api_views.py         # REST API ViewSets
    ├── api_urls.py          # API URL configuration
    ├── serializers.py       # DRF serializers
    ├── permissions.py       # Custom permissions
    ├── signals.py           # Post-approval signal handlers
    ├── tests.py             # Unit tests
    ├── apps.py              # App configuration
    ├── templates/news/      # Bootstrap 5 HTML templates
    │   ├── base.html        # Base template with Bootstrap navbar
    │   ├── dashboard.html   # Role-specific dashboard
    │   ├── article_list.html
    │   ├── article_detail.html
    │   ├── pending_articles.html
    │   ├── newsletter_list.html
    │   └── newsletter_detail.html
    └── management/
        └── commands/
            └── setup_groups.py  # Group setup command
```

## Technologies Used

### Backend
- **Django 4.2.27**: Web framework with MVT architecture
- **Django REST Framework 3.16.1**: RESTful API development
- **djangorestframework-simplejwt 5.5.1**: JWT authentication
- **MariaDB** (via mysqlclient 2.1.1): Production database
- **Pillow 11.3.0**: Image handling
- **Requests 2.31.0**: Twitter/X API integration

### Frontend
- **Bootstrap 5.3.2**: Modern, responsive CSS framework
- **Bootstrap Icons 1.11.3**: Icon library
- **Google Fonts**: Playfair Display & Lora typography
- **Custom CSS**: Professional color scheme and animations

## Code Quality Features

- ✅ Comprehensive docstrings for all classes and functions
- ✅ Defensive coding with input validation
- ✅ Exception handling throughout
- ✅ Type hints where applicable
- ✅ Modular, reusable code
- ✅ Clean, readable code with descriptive variable names
- ✅ Proper indentation and whitespace
- ✅ Security best practices (authentication, authorization, CSRF protection)
- ✅ Professional UI/UX with Bootstrap 5
- ✅ Mobile-responsive design
- ✅ Accessibility considerations

## Security Considerations

- JWT token-based authentication
- Role-based access control enforced at multiple levels
- CSRF protection enabled
- Password validation
- Input validation on models and serializers
- SQL injection protection (Django ORM)
- Defense in depth: permissions checked in views AND serializers
- Secure headers and cookie settings

## Screenshots & Demo

The application features a **professional, magazine-style design** with:

- 📰 Clean, readable article layouts with elegant typography
- 🎨 Modern gradient color schemes (dark blues with red accents)
- 💼 Professional dashboard views tailored to each user role
- 📱 Fully responsive design for mobile, tablet, and desktop
- ✨ Smooth animations and hover effects
- 🎯 Intuitive navigation with icon-based menus

## Future Enhancements

- Advanced search and filtering
- Article categories and tags
- Comment system
- Rich text editor integration
- Article analytics and view counts
- Social media sharing buttons
- RSS feeds
- Email digest scheduling

## License

This project is for educational purposes.

## Author

Created as part of a Django development task focusing on:
- Database normalization
- Role-based access control
- RESTful API design
- Signal-based automation
- Comprehensive testing
