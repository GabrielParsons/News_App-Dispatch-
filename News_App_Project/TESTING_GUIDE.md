# Testing Guide for Fixed Features

## Quick Start Testing

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Migrations (if needed)
```bash
python manage.py migrate
```

### 3. Create Test Users
```bash
python manage.py shell
```

Then in the Python shell:
```python
from news.models import CustomUser, Publisher

# Create a superuser (admin)
admin = CustomUser.objects.create_superuser(
    username='admin',
    email='admin@test.com',
    password='admin123',
    role='editor'
)

# Create test journalist
journalist = CustomUser.objects.create_user(
    username='journalist1',
    email='journalist@test.com',
    password='test123',
    role='journalist',
    first_name='John',
    last_name='Writer'
)

# Create test editor
editor = CustomUser.objects.create_user(
    username='editor1',
    email='editor@test.com',
    password='test123',
    role='editor',
    first_name='Jane',
    last_name='Editor'
)

# Create test reader
reader = CustomUser.objects.create_user(
    username='reader1',
    email='reader@test.com',
    password='test123',
    role='reader',
    first_name='Bob',
    last_name='Reader'
)

# Create a test publisher
publisher = Publisher.objects.create(
    name='Tech News Daily',
    description='Latest technology news and updates',
    website='https://technews.example.com'
)

exit()
```

## Test Scenarios

### Scenario 1: Journalist Creates Article (NEW FEATURE)

1. **Login as journalist**
   - Username: `journalist1`
   - Password: `test123`

2. **Navigate to Dashboard**
   - You should see a green "Create New Article" button
   - Button should be clearly visible (not white)

3. **Click "Create New Article"**
   - You should see a form (NOT the admin page)
   - Form should have: Title, Content, Publisher fields

4. **Fill out the form**
   ```
   Title: My First Article
   Content: This is a test article about technology.
   Publisher: (leave blank or select Tech News Daily)
   ```

5. **Submit the form**
   - Should redirect to article detail page
   - Article should show "Pending Approval" badge
   - Should NOT be able to access /admin/ page

### Scenario 2: Editor Approves Article

1. **Login as editor**
   - Username: `editor1`
   - Password: `test123`

2. **Navigate to Dashboard**
   - Should see "X article(s) awaiting approval"

3. **Click "Review Pending Articles"**
   - Should see the article created by journalist

4. **Click on the article**
   - Should see "Approve Article" and "Reject Article" buttons at bottom

5. **Click "Approve Article"**
   - Should see success message
   - Article should now be approved
   - If Twitter is configured, should post to Twitter

### Scenario 3: Reader Subscribes to Journalist (NEW FEATURE)

1. **Login as reader**
   - Username: `reader1`
   - Password: `test123`

2. **Navigate to Articles page**
   - Click on an approved article

3. **Scroll to bottom of article**
   - Should see "Stay Updated" section
   - Should see "Subscribe to John Writer" button
   - Button should be clearly visible (burgundy/red color)

4. **Click Subscribe button**
   - Should see success message "Subscribed to John Writer"
   - Button should change to "Subscribed to John Writer" (gray outline)

5. **Click the "Subscriptions" link in navbar**
   - Should see browse subscriptions page
   - Should see Tech News Daily publisher listed
   - Should see John Writer journalist listed
   - John Writer should show "Subscribed" button

6. **Test unsubscribe**
   - Click "Subscribed" button next to John Writer
   - Should see "Unsubscribed" message
   - Button should change back to "Subscribe"

### Scenario 4: Journalist Creates Newsletter (NEW FEATURE)

1. **Login as journalist**
   - Username: `journalist1`
   - Password: `test123`

2. **Wait for article to be approved** (complete Scenario 2 first)

3. **Navigate to Dashboard**
   - Should see blue "Create New Newsletter" button
   - Button should be clearly visible

4. **Click "Create New Newsletter"**
   - Should see newsletter form (NOT admin page)
   - Should see approved articles in checkbox list

5. **Fill out form**
   ```
   Title: Weekly Tech Roundup
   Description: Best tech articles of the week
   Articles: Select "My First Article"
   ```

6. **Submit form**
   - Should redirect to newsletter detail page
   - Should show selected article

### Scenario 5: Admin Access Restriction (SECURITY FIX)

1. **Login as journalist or editor** (NOT admin)
   - Username: `journalist1` or `editor1`
   - Password: `test123`

2. **Try to access /admin/**
   - Type in browser: `http://localhost:8000/admin/`
   - Should be denied access (403 or redirect)

3. **Logout and login as admin**
   - Username: `admin`
   - Password: `admin123`

4. **Access /admin/**
   - Should be able to access admin panel
   - This confirms only superusers can access admin

### Scenario 6: Button Visibility (UI FIX)

1. **Login as any user**

2. **Check Dashboard**
   - All buttons should be visible WITHOUT hovering
   - Buttons should have distinct colors:
     - Green for "Create Article"
     - Blue for "Create Newsletter"
     - Burgundy/Red for other primary actions

3. **Hover over buttons**
   - Should see subtle animation (move up slightly)
   - Should see shadow appear

## Twitter Integration Testing

### Setup Twitter Credentials

1. **Get Twitter API credentials** from https://developer.twitter.com

2. **Update settings.py**:
   ```python
   TWITTER_API_KEY = 'your-actual-api-key'
   TWITTER_API_SECRET = 'your-actual-api-secret'
   TWITTER_ACCESS_TOKEN = 'your-actual-access-token'
   TWITTER_ACCESS_TOKEN_SECRET = 'your-actual-access-secret'
   ```

3. **Test posting**:
   - Create and approve an article (Scenarios 1 & 2)
   - Check your Twitter account
   - Should see a new tweet with article title and preview

### What Changed with Twitter
- **Before**: Used only Bearer token (didn't work for posting)
- **After**: Uses OAuth 1.0a with all 4 credentials (works correctly)

## Verification Checklist

- [ ] Journalist can create articles via frontend form (not admin)
- [ ] Journalist can create newsletters via frontend form (not admin)
- [ ] Buttons are visible without hover (green, blue, burgundy colors)
- [ ] Reader can subscribe to journalist from article detail page
- [ ] Reader can subscribe to publisher from article detail page
- [ ] Reader can browse all subscriptions from "Subscriptions" page
- [ ] Reader can unsubscribe by clicking again
- [ ] Only superusers can access /admin/ page
- [ ] Regular users (journalist, editor, reader) cannot access admin
- [ ] Twitter posting works with OAuth 1.0a (if configured)

## Common Issues

### Issue: "Module 'requests_oauthlib' not found"
**Solution**: Run `pip install requests-oauthlib`

### Issue: Can't create article - form validation error
**Solution**: Make sure to fill in both Title and Content (required fields)

### Issue: Newsletter has no articles to select
**Solution**: Create and approve at least one article first

### Issue: Subscription button not showing
**Solution**: Make sure you're logged in as a reader and viewing an approved article

### Issue: Twitter posting fails
**Solution**: 
1. Check all 4 credentials are set in settings.py
2. Make sure they're not placeholder values
3. Verify Twitter app has "Read and Write" permissions
4. Check application logs for error details

## Next Steps

After testing, you can:
1. Create more test content
2. Test the REST API endpoints
3. Customize the styling further
4. Deploy to production

For API testing, see `API_TESTING_GUIDE.md`
