from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from markupsafe import Markup
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from authlib.integrations.flask_client import OAuth
from email_validator import validate_email, EmailNotValidError
from datetime import datetime, timedelta
import os
import requests
import stripe
from bs4 import BeautifulSoup
import re
import random
import json
import bleach
import logging
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging first
logging.basicConfig(
    level=logging.DEBUG if os.environ.get('FLASK_ENV') != 'production' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Security Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # CSRF token expires in 1 hour
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', '3600')))

# Database configuration with better fallbacks
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Handle Heroku postgres URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://')
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    # Hide credentials in logs safely
    try:
        if '@' in database_url:
            safe_url = database_url.split('@')[0] + '@***'
        else:
            safe_url = database_url
        logger.info(f"Using database: {safe_url}")
    except:
        logger.info("Using configured database")
else:
    # Default to SQLite for development
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///seo_tool.db'
    logger.info("Using SQLite database for development")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Google OAuth Config
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET')

# Stripe Config
app.config['STRIPE_PUBLISHABLE_KEY'] = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_51234567890abcdef')  # Test key for development
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_51234567890abcdef')  # Test key for development
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Rate Limiting Config
app.config['RATELIMIT_STORAGE_URL'] = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'info'

# Rate limiting setup
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri=app.config['RATELIMIT_STORAGE_URL']
)

# OAuth setup - only if credentials are provided
oauth = OAuth(app)
google = None

# Only initialize Google OAuth if real credentials are available (not demo)
client_id = app.config.get('GOOGLE_CLIENT_ID')
client_secret = app.config.get('GOOGLE_CLIENT_SECRET')

if client_id and client_secret:
    try:
        google = oauth.register(
            name='google',
            client_id=client_id,
            client_secret=client_secret,
            server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
            client_kwargs={
                'scope': 'openid email profile'
            }
        )
        logger.info("✅ Google OAuth initialized successfully with real credentials")
    except Exception as e:
        logger.error(f"⚠️ Google OAuth initialization failed: {e}")
        google = None
else:
    logger.info("ℹ️ Google OAuth not configured - only email/password authentication available")

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Security headers - simplified for debugging
@app.after_request
def security_headers(response):
    # Minimal headers for debugging
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    return response

# Input sanitization utility
def sanitize_input(text, allowed_tags=None):
    """Sanitize user input to prevent XSS attacks"""
    if not text:
        return ''
    
    if allowed_tags is None:
        allowed_tags = []
    
    return bleach.clean(str(text), tags=allowed_tags, strip=True)

# Template context processor to make Google OAuth status available
@app.context_processor
def inject_google_oauth_status():
    return {'google_oauth_enabled': google is not None}

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(60), nullable=True)  # Null for OAuth users
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    plan = db.Column(db.String(20), default='trial')  # trial, starter, professional, enterprise
    trial_end = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Stripe payment fields
    stripe_customer_id = db.Column(db.String(100), nullable=True)
    stripe_subscription_id = db.Column(db.String(100), nullable=True)
    subscription_status = db.Column(db.String(20), default='trialing')  # trialing, active, past_due, canceled
    current_period_end = db.Column(db.DateTime, nullable=True)
    
    # Usage tracking
    daily_keyword_queries = db.Column(db.Integer, default=0)
    daily_seo_reports = db.Column(db.Integer, default=0)
    last_usage_reset = db.Column(db.Date, default=datetime.utcnow().date)
    
    # Relationships
    tracked_keywords = db.relationship('TrackedKeyword', backref='user', lazy=True)
    seo_analyses = db.relationship('SEOAnalysis', backref='user', lazy=True)
    
    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_trial_active(self):
        if self.trial_end:
            return datetime.utcnow() < self.trial_end
        return False
    
    def get_plan_limits(self):
        limits = {
            'trial': {'keyword_queries': 50, 'seo_reports': 20, 'tracked_keywords': 100},
            'starter': {'keyword_queries': 25, 'seo_reports': 5, 'tracked_keywords': 10},  # Weekly limits
            'professional': {'keyword_queries': 500, 'seo_reports': 50, 'tracked_keywords': 100}  # Monthly limits
        }
        current_plan = 'trial' if self.is_trial_active() else self.plan
        return limits.get(current_plan, limits['starter'])
    
    def is_professional(self):
        """Check if user has professional plan"""
        return self.plan == 'professional' and not self.is_trial_active()
    
    def can_export_csv(self):
        """Check if user can export CSV files"""
        return self.is_professional() or self.is_trial_active()
    
    def can_access_historical_data(self):
        """Check if user can access historical data beyond 7 days"""
        return self.is_professional() or self.is_trial_active()
    
    def can_track_more_keywords(self):
        """Check if user can track more keywords"""
        limits = self.get_plan_limits()
        current_tracked = TrackedKeyword.query.filter_by(user_id=self.id).count()
        return current_tracked < limits['tracked_keywords']
    
    def get_plan_display_name(self):
        """Get display name for current plan"""
        if self.is_trial_active():
            return "Trial"
        elif self.plan == 'professional':
            return "Professional"
        else:
            return "Starter"
    
    def reset_daily_usage_if_needed(self):
        today = datetime.utcnow().date()
        if self.last_usage_reset != today:
            self.daily_keyword_queries = 0
            self.daily_seo_reports = 0
            self.last_usage_reset = today
            db.session.commit()
    
    def can_use_feature(self, feature_type):
        self.reset_daily_usage_if_needed()
        limits = self.get_plan_limits()
        
        if feature_type == 'keyword_queries':
            limit = limits['keyword_queries']
            return limit == -1 or self.daily_keyword_queries < limit
        elif feature_type == 'seo_reports':
            limit = limits['seo_reports']
            return limit == -1 or self.daily_seo_reports < limit
        elif feature_type == 'tracked_keywords':
            limit = limits['tracked_keywords']
            current_count = len(self.tracked_keywords)
            return limit == -1 or current_count < limit
        
        return False

class TrackedKeyword(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(255), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rankings = db.relationship('Ranking', backref='tracked_keyword', lazy=True)

class Ranking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    keyword_id = db.Column(db.Integer, db.ForeignKey('tracked_keyword.id'), nullable=False)
    position = db.Column(db.Integer)
    url = db.Column(db.String(500))
    checked_at = db.Column(db.DateTime, default=datetime.utcnow)

class SEOAnalysis(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(255))
    meta_description = db.Column(db.Text)
    h1_tags = db.Column(db.Text)
    word_count = db.Column(db.Integer)
    analysis_score = db.Column(db.Integer)
    issues = db.Column(db.Text)  # JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Routes
@app.route('/test')
@csrf.exempt
def test():
    """Simple test route with plain HTML"""
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="format-detection" content="telephone=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>Test Page - Safari Debug</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 8px;
            max-width: 600px;
            margin: 0 auto;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #2563eb; }
        .status { 
            background: #10b981; 
            color: white; 
            padding: 10px 20px; 
            border-radius: 4px; 
            display: inline-block;
            margin: 10px 0;
        }
        .info { background: #f3f4f6; padding: 15px; border-radius: 4px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧪 Safari Test Page</h1>
        <div class="status">✅ Flask Backend Working</div>
        <div class="info">
            <strong>Test Results:</strong><br>
            • HTML Rendering: ✅ Working<br>
            • CSS Styling: ✅ Working<br>
            • Safari Compatibility: ✅ Working
        </div>
        <p>If you can see this styled page, then:</p>
        <ul>
            <li>Flask is serving content correctly</li>
            <li>Safari can render HTML + CSS</li>
            <li>The issue is with the main templates</li>
        </ul>
        <p><a href="/" style="color: #2563eb;">← Try Main Page</a></p>
    </div>
</body>
</html>"""

@app.route('/health')
@csrf.exempt
def health():
    """Health check endpoint for debugging"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = "OK"
    except Exception as e:
        db_status = f"ERROR: {str(e)}"
    
    return jsonify({
        'status': 'OK',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat(),
        'flask_env': os.environ.get('FLASK_ENV', 'not_set'),
        'user_agent': request.headers.get('User-Agent', 'not_provided')
    })

@app.route('/')
@csrf.exempt
def index():
    try:
        logger.info("=== INDEX ROUTE ACCESSED ===")
        logger.info(f"User agent: {request.headers.get('User-Agent', 'not_provided')}")
        
        # Render the original beautiful template
        logger.info("Rendering original index.html template")
        result = render_template('index.html')
        logger.info(f"Template rendered successfully, length: {len(result)}")
        return result
    except Exception as e:
        logger.error(f"ERROR in index route: {str(e)}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return f"<html><body><h1>Template Error</h1><p>Error: {str(e)}</p><pre>{traceback.format_exc()}</pre></body></html>", 500

@app.route('/keyword-research')
def keyword_research():
    return render_template('keyword_research.html')

@app.route('/api/keyword-research', methods=['POST'])
@limiter.limit("20 per hour")  # Limit keyword research requests
def api_keyword_research():
    # Check usage limits only for authenticated users
    if current_user.is_authenticated:
        if not current_user.can_use_feature('keyword_queries'):
            limits = current_user.get_plan_limits()
            return jsonify({
                'error': f'Daily limit reached. You can perform {limits["keyword_queries"]} keyword queries per day with your current plan.',
                'upgrade_required': True
            }), 429
    
    data = request.get_json()
    keyword = sanitize_input(data.get('keyword', '')).strip()
    
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400
    
    # Get keyword suggestions from Google Suggest API
    suggestions = get_keyword_suggestions(keyword)
    
    # Generate realistic mock data for MVP
    results = []
    base_volume = random.randint(500, 5000)
    
    for i, suggestion in enumerate(suggestions[:15]):
        # Generate realistic metrics
        volume_multiplier = 1 - (i * 0.1)  # Decreasing volume for longer tail
        search_volume = max(50, int(base_volume * volume_multiplier))
        
        # Difficulty based on keyword length and competition
        difficulty = min(90, 20 + len(suggestion.split()) * 10 + random.randint(0, 30))
        
        # CPC based on commercial intent
        commercial_keywords = ['buy', 'price', 'cost', 'cheap', 'best', 'review']
        is_commercial = any(word in suggestion.lower() for word in commercial_keywords)
        base_cpc = random.uniform(1.5, 8.0) if is_commercial else random.uniform(0.3, 2.0)
        
        # Generate realistic trend data
        trend_weights = []
        if is_commercial:
            # Commercial keywords more likely to trend up
            trend_weights = ['up'] * 40 + ['stable'] * 35 + ['down'] * 25
        elif len(suggestion.split()) >= 3:
            # Long-tail keywords more likely to be stable
            trend_weights = ['stable'] * 50 + ['up'] * 25 + ['down'] * 25
        else:
            # Short competitive keywords have mixed trends
            trend_weights = ['up'] * 30 + ['stable'] * 40 + ['down'] * 30
        
        trend = random.choice(trend_weights)
        
        results.append({
            'keyword': suggestion,
            'search_volume': f"{search_volume:,}",
            'difficulty': difficulty,
            'cpc': f"${base_cpc:.2f}",
            'trend': trend
        })
    
    # Increment usage counter only for authenticated users
    if current_user.is_authenticated:
        current_user.daily_keyword_queries += 1
        db.session.commit()
    
    return jsonify({'keywords': results})

def get_keyword_suggestions(keyword):
    """Get keyword suggestions from Google Suggest API"""
    try:
        # Google Suggest API (free and doesn't require API key)
        url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={keyword}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            suggestions = response.json()[1]
            return suggestions[:15]  # Limit to 15 suggestions
    except Exception as e:
        print(f"Error fetching suggestions: {e}")
    
    # Fallback: generate basic variations
    return [
        keyword,
        f"{keyword} tips",
        f"{keyword} guide",
        f"best {keyword}",
        f"{keyword} tutorial",
        f"how to {keyword}",
        f"{keyword} examples"
    ]

@app.route('/seo-checker')
def seo_checker():
    return render_template('seo_checker.html')

@app.route('/api/seo-analysis', methods=['POST'])
@login_required
@limiter.limit("10 per hour")  # Limit SEO analysis requests
def api_seo_analysis():
    # Check usage limits
    if not current_user.can_use_feature('seo_reports'):
        limits = current_user.get_plan_limits()
        return jsonify({
            'error': f'Daily limit reached. You can perform {limits["seo_reports"]} SEO reports per day with your current plan.',
            'upgrade_required': True
        }), 429
    
    data = request.get_json()
    url = sanitize_input(data.get('url', '')).strip()
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Check if we have a recent analysis cached for this user
    recent_analysis = SEOAnalysis.query.filter(
        SEOAnalysis.url == url,
        SEOAnalysis.user_id == current_user.id,
        SEOAnalysis.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).first()
    
    if recent_analysis:
        return jsonify({
            'url': recent_analysis.url,
            'title': recent_analysis.title,
            'title_length': len(recent_analysis.title) if recent_analysis.title else 0,
            'meta_description': recent_analysis.meta_description,
            'meta_description_length': len(recent_analysis.meta_description) if recent_analysis.meta_description else 0,
            'h1_tags': json.loads(recent_analysis.h1_tags) if recent_analysis.h1_tags else [],
            'word_count': recent_analysis.word_count,
            'score': recent_analysis.analysis_score,
            'issues': json.loads(recent_analysis.issues) if recent_analysis.issues else [],
            'cached': True
        })
    
    # Perform new analysis with plan-based limitations
    is_professional = current_user.is_professional()
    analysis = analyze_page_seo(url, is_professional)
    
    if 'error' in analysis:
        return jsonify(analysis), 400
    
    # Save to database and increment usage counter
    try:
        seo_analysis = SEOAnalysis(
            url=url,
            user_id=current_user.id,
            title=analysis.get('title', ''),
            meta_description=analysis.get('meta_description', ''),
            h1_tags=json.dumps(analysis.get('h1_tags', [])),
            word_count=analysis.get('word_count', 0),
            analysis_score=analysis.get('score', 0),
            issues=json.dumps(analysis.get('issues', []))
        )
        db.session.add(seo_analysis)
        
        # Increment usage counter
        current_user.daily_seo_reports += 1
        db.session.commit()
    except Exception as e:
        print(f"Error saving analysis: {e}")
        db.session.rollback()
    
    return jsonify(analysis)

def analyze_page_seo(url, is_professional=False):
    """Analyze on-page SEO factors with plan-based limitations"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract SEO elements
        title = soup.find('title')
        title_text = title.text.strip() if title else ''
        
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '').strip() if meta_desc else ''
        
        # Get all heading tags
        h1_tags = [h1.text.strip() for h1 in soup.find_all('h1')]
        h2_tags = [h2.text.strip() for h2 in soup.find_all('h2')]
        h3_tags = [h3.text.strip() for h3 in soup.find_all('h3')]
        
        # Remove script and style elements for word count
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Word count
        text_content = soup.get_text()
        words = text_content.split()
        word_count = len([word for word in words if len(word) > 2])
        
        # Image analysis
        images = soup.find_all('img')
        images_without_alt = len([img for img in images if not img.get('alt')])
        
        # SEO Analysis and Scoring
        issues = []
        recommendations = []
        score = 100
        
        # Title tag analysis
        if not title_text:
            issues.append("Missing title tag")
            score -= 20
        elif len(title_text) < 30:
            issues.append("Title tag too short (< 30 characters)")
            score -= 10
        elif len(title_text) > 60:
            issues.append("Title tag too long (> 60 characters)")
            score -= 5
        
        # Meta description analysis
        if not meta_desc_text:
            issues.append("Missing meta description")
            score -= 15
        elif len(meta_desc_text) < 120:
            issues.append("Meta description too short (< 120 characters)")
            score -= 10
        elif len(meta_desc_text) > 160:
            issues.append("Meta description too long (> 160 characters)")
            score -= 5
        
        # H1 tag analysis
        if len(h1_tags) == 0:
            issues.append("Missing H1 tag")
            score -= 15
        elif len(h1_tags) > 1:
            issues.append("Multiple H1 tags found")
            score -= 10
        
        # Content length
        if word_count < 300:
            issues.append("Content too short (< 300 words)")
            score -= 10
        elif word_count > 2000:
            recommendations.append("Consider breaking up long content")
        
        # Image alt tags
        if images_without_alt > 0:
            issues.append(f"{images_without_alt} images missing alt attributes")
            score -= min(15, images_without_alt * 2)
        
        # URL structure
        if len(url) > 100:
            issues.append("URL is very long")
            score -= 5
        
        # Generate recommendations
        if len(title_text) < 50:
            recommendations.append("Consider making title more descriptive")
        if len(meta_desc_text) < 140:
            recommendations.append("Expand meta description to 140-160 characters")
        if word_count < 500:
            recommendations.append("Add more content to improve SEO value")
        if len(h2_tags) < 2:
            recommendations.append("Add more H2 headings to structure content")
        
        score = max(0, score)
        
        # Limit data for Starter users
        if not is_professional:
            # Starter users get basic report only
            return {
                'url': url,
                'title': title_text,
                'title_length': len(title_text),
                'meta_description': meta_desc_text,
                'meta_description_length': len(meta_desc_text),
                'h1_tags': h1_tags[:1],  # Only first H1
                'h2_tags': [],  # No H2 tags for Starter
                'h3_tags': [],  # No H3 tags for Starter
                'word_count': word_count,
                'image_count': len(images),
                'images_without_alt': len(images_without_alt),  # Just count, not list
                'issues': issues[:5],  # Only top 5 issues
                'recommendations': recommendations[:3],  # Only top 3 recommendations
                'score': score,
                'limited': True,
                'upgrade_message': 'Upgrade to Professional for complete SEO analysis including all heading tags, detailed recommendations, and advanced insights.'
            }
        
        # Professional users get full report
        return {
            'url': url,
            'title': title_text,
            'title_length': len(title_text),
            'meta_description': meta_desc_text,
            'meta_description_length': len(meta_desc_text),
            'h1_tags': h1_tags,
            'h2_tags': h2_tags[:5],  # First 5 H2 tags
            'h3_tags': h3_tags[:3],  # First 3 H3 tags
            'word_count': word_count,
            'image_count': len(images),
            'images_without_alt': images_without_alt,
            'issues': issues,
            'recommendations': recommendations,
            'score': score,
            'limited': False
        }
        
    except requests.exceptions.RequestException as e:
        return {'error': f'Failed to fetch URL: {str(e)}'}
    except Exception as e:
        return {'error': f'Failed to analyze page: {str(e)}'}

@app.route('/rank-tracker')
@login_required
def rank_tracker():
    tracked_keywords = TrackedKeyword.query.filter_by(user_id=current_user.id).order_by(TrackedKeyword.created_at.desc()).all()
    return render_template('rank_tracker.html', keywords=tracked_keywords)

@app.route('/pricing')
def pricing():
    return render_template('pricing.html')

# Stripe Payment Routes
@app.route('/subscribe/<plan_name>')
def subscribe(plan_name):
    """Create Stripe checkout session for subscription"""
    
    # If user is not logged in, redirect to signup with plan info
    if not current_user.is_authenticated:
        flash(f'Please sign up to subscribe to the {plan_name.title()} plan.', 'info')
        session['selected_plan'] = plan_name  # Store plan selection for after signup
        return redirect(url_for('signup'))
    # Define plan configurations
    plans = {
        'starter': {
            'price_id': 'price_starter_weekly',  # Replace with actual Stripe price ID
            'name': 'Starter Plan',
            'amount': 900,  # $9.00 per week in cents
            'interval': 'week'
        },
        'professional': {
            'price_id': 'price_professional_monthly',  # Replace with actual Stripe price ID
            'name': 'Professional Plan', 
            'amount': 2900,  # $29.00 per month in cents
            'interval': 'month'
        }
    }
    
    if plan_name not in plans:
        flash('Invalid plan selected.', 'error')
        return redirect(url_for('pricing'))
    
    plan = plans[plan_name]
    
    try:
        # For development/testing: simulate payment process if Stripe not configured properly
        if app.config['STRIPE_SECRET_KEY'].startswith('sk_test_51234567890'):
            # Demo mode - simulate subscription for both plans
            interval_text = 'week' if plan_name == 'starter' else 'month'
            flash(f'✅ DEMO MODE: Successfully "subscribed" to {plan["name"]} (${plan["amount"]/100:.2f}/{interval_text}). This is a simulation - configure real Stripe keys for actual payments.', 'success')
            
            # Update user's plan in database
            current_user.plan = plan_name
            current_user.subscription_status = 'active'
            current_user.trial_end = None  # End trial when subscribing
            db.session.commit()
            
            return redirect(url_for('dashboard'))
        
        # Create or retrieve Stripe customer
        if current_user.stripe_customer_id:
            customer_id = current_user.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
            )
            current_user.stripe_customer_id = customer.id
            db.session.commit()
            customer_id = customer.id
        
        # Create Stripe checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': plan['name'],
                        'description': f'Monthly subscription to {plan["name"]}',
                    },
                    'unit_amount': plan['amount'],
                    'recurring': {
                        'interval': 'month',
                    },
                },
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('pricing', _external=True),
            metadata={
                'user_id': current_user.id,
                'plan_name': plan_name,
            }
        )
        
        return redirect(checkout_session.url, code=303)
        
    except stripe.error.StripeError as e:
        flash(f'Payment error: {str(e)}', 'error')
        return redirect(url_for('pricing'))
    except Exception as e:
        flash('An error occurred. Please try again.', 'error')
        return redirect(url_for('pricing'))

@app.route('/payment/success')
@login_required
def payment_success():
    """Handle successful payment"""
    session_id = request.args.get('session_id')
    if not session_id:
        flash('Invalid payment session.', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        # Retrieve the checkout session
        checkout_session = stripe.checkout.Session.retrieve(session_id)
        
        if checkout_session.payment_status == 'paid':
            # Update user's subscription status
            current_user.subscription_status = 'active'
            current_user.plan = checkout_session.metadata.get('plan_name', 'starter')
            
            # Get subscription details
            if checkout_session.subscription:
                subscription = stripe.Subscription.retrieve(checkout_session.subscription)
                current_user.stripe_subscription_id = subscription.id
                current_user.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
            
            db.session.commit()
            flash('Payment successful! Your subscription is now active.', 'success')
        else:
            flash('Payment was not completed. Please try again.', 'error')
            
    except stripe.error.StripeError as e:
        flash(f'Error verifying payment: {str(e)}', 'error')
    except Exception as e:
        flash('An error occurred verifying your payment.', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/payment/cancel')
@login_required  
def payment_cancel():
    """Handle cancelled payment"""
    flash('Payment was cancelled.', 'info')
    return redirect(url_for('pricing'))

@app.route('/webhook/stripe', methods=['POST'])
@csrf.exempt  # Stripe webhooks don't include CSRF tokens
def stripe_webhook():
    """Handle Stripe webhook events"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    
    # You'll need to set this in production
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', 'whsec_test_webhook_secret')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        # Invalid payload
        return 'Invalid payload', 400
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return 'Invalid signature', 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        # Payment was successful
        session = event['data']['object']
        handle_successful_payment(session)
        
    elif event['type'] == 'invoice.payment_succeeded':
        # Monthly payment succeeded
        invoice = event['data']['object']
        handle_subscription_payment(invoice)
        
    elif event['type'] == 'invoice.payment_failed':
        # Payment failed
        invoice = event['data']['object']
        handle_payment_failed(invoice)
        
    elif event['type'] == 'customer.subscription.deleted':
        # Subscription was cancelled
        subscription = event['data']['object']
        handle_subscription_cancelled(subscription)
    
    return 'Success', 200

def handle_successful_payment(session):
    """Handle successful payment from webhook"""
    try:
        user_id = session.get('metadata', {}).get('user_id')
        plan_name = session.get('metadata', {}).get('plan_name')
        
        if user_id and plan_name:
            user = User.query.get(user_id)
            if user:
                user.subscription_status = 'active'
                user.plan = plan_name
                
                # Get subscription details
                if session.get('subscription'):
                    subscription = stripe.Subscription.retrieve(session['subscription'])
                    user.stripe_subscription_id = subscription.id
                    user.current_period_end = datetime.fromtimestamp(subscription.current_period_end)
                
                db.session.commit()
                logger.info(f"User {user_id} subscription activated: {plan_name}")
                
    except Exception as e:
        logger.error(f"Error handling successful payment: {str(e)}")

def handle_subscription_payment(invoice):
    """Handle recurring subscription payment"""
    try:
        customer_id = invoice.get('customer')
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            user.subscription_status = 'active'
            # Reset usage counters on successful payment
            user.daily_keyword_queries = 0
            user.daily_seo_reports = 0
            user.last_usage_reset = datetime.utcnow().date()
            db.session.commit()
            logger.info(f"Subscription payment succeeded for user {user.id}")
            
    except Exception as e:
        logger.error(f"Error handling subscription payment: {str(e)}")

def handle_payment_failed(invoice):
    """Handle failed payment"""
    try:
        customer_id = invoice.get('customer')
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            user.subscription_status = 'past_due'
            db.session.commit()
            logger.warning(f"Payment failed for user {user.id}")
            
    except Exception as e:
        logger.error(f"Error handling payment failure: {str(e)}")

def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    try:
        customer_id = subscription.get('customer')
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            user.subscription_status = 'canceled'
            user.plan = 'trial'  # Revert to trial
            user.stripe_subscription_id = None
            db.session.commit()
            logger.info(f"Subscription cancelled for user {user.id}")
            
    except Exception as e:
        logger.error(f"Error handling subscription cancellation: {str(e)}")

# Authentication Routes
@app.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Limit signup attempts
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = sanitize_input(data.get('email', '')).strip().lower()
        name = sanitize_input(data.get('name', '')).strip()
        password = data.get('password', '')  # Don't sanitize passwords
        
        # Validate email
        try:
            validate_email(email)
        except EmailNotValidError:
            if request.is_json:
                return jsonify({'error': 'Invalid email address'}), 400
            flash('Invalid email address', 'danger')
            return render_template('auth/signup.html')
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'error': 'Email already registered'}), 400
            flash('Email already registered. Please log in.', 'danger')
            return render_template('auth/signup.html')
        
        # Create new user
        user = User(
            email=email,
            name=name or email.split('@')[0],
            trial_end=datetime.utcnow() + timedelta(days=7)
        )
        
        if password:
            user.set_password(password)
        
        try:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('dashboard')})
            flash('Welcome! Your 7-day trial has started.', 'success')
            
            # Check if user had selected a plan before signup
            selected_plan = session.pop('selected_plan', None)
            if selected_plan:
                return redirect(url_for('subscribe', plan_name=selected_plan))
            
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'error': 'Registration failed'}), 500
            flash('Registration failed. Please try again.', 'danger')
    
    return render_template('auth/signup.html')

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")  # Limit login attempts
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        email = sanitize_input(data.get('email', '')).strip().lower()
        password = data.get('password', '')  # Don't sanitize passwords
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.password_hash and user.check_password(password):
            login_user(user, remember=data.get('remember', False))
            next_page = request.args.get('next')
            
            # Check if user had selected a plan before login
            selected_plan = session.pop('selected_plan', None)
            if selected_plan and not next_page:
                next_page = url_for('subscribe', plan_name=selected_plan)
            
            if request.is_json:
                return jsonify({'success': True, 'redirect': next_page or url_for('dashboard')})
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            if request.is_json:
                return jsonify({'error': 'Invalid email or password'}), 400
            flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html')

@app.route('/auth/google')
def google_auth():
    if not google:
        flash('Google Sign-In requires proper Google Cloud credentials. Please set up your Google OAuth credentials or use email/password authentication.', 'warning')
        return redirect(url_for('login'))
    
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    if not google:
        flash('Google authentication is not configured.', 'warning')
        return redirect(url_for('login'))
    
    try:
        token = google.authorize_access_token()
        
        # Parse the ID token to get user info
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback to making a request to userinfo endpoint
            nonce = session.get('google_auth_nonce')
            user_info = google.parse_id_token(token, nonce=nonce)
        
        if user_info and 'email' in user_info:
            email = user_info['email'].lower()
            name = user_info.get('name', email.split('@')[0])
            google_id = user_info.get('sub', user_info.get('id'))  # 'sub' is standard, 'id' is fallback
            
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    google_id=google_id,
                    trial_end=datetime.utcnow() + timedelta(days=7)
                )
                db.session.add(user)
                db.session.commit()
                flash('Welcome! Your 7-day trial has started.', 'success')
            else:
                # Update existing user with Google ID if not set
                if not user.google_id:
                    user.google_id = google_id
                    db.session.commit()
            
            login_user(user)
            return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}")
        logger.error(f"Full error: {traceback.format_exc()}")
        flash(f'Google authentication failed: {str(e)}. Please try again or use email/password login.', 'danger')
    
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/test-plan/<plan_name>')
@login_required
def test_plan_switch(plan_name):
    """Test route to quickly switch plans in demo mode"""
    # Only allow in demo mode
    if not app.config['STRIPE_SECRET_KEY'].startswith('sk_test_51234567890'):
        flash('This feature is only available in demo mode.', 'warning')
        return redirect(url_for('dashboard'))
    
    if plan_name not in ['starter', 'professional', 'trial']:
        flash('Invalid plan name.', 'error')
        return redirect(url_for('dashboard'))
    
    if plan_name == 'trial':
        current_user.plan = 'starter'
        current_user.trial_end = datetime.utcnow() + timedelta(days=7)
        flash('✅ TEST MODE: Switched to 7-day trial.', 'success')
    else:
        current_user.plan = plan_name
        current_user.trial_end = None
        current_user.subscription_status = 'active'
        flash(f'✅ TEST MODE: Switched to {plan_name.title()} plan. Test the different features!', 'success')
    
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    user = current_user
    user.reset_daily_usage_if_needed()
    
    # Get user statistics
    total_keywords = len(user.tracked_keywords)
    total_analyses = len(user.seo_analyses)
    
    # Get plan limits
    limits = user.get_plan_limits()
    
    # Recent activity
    recent_keywords = TrackedKeyword.query.filter_by(user_id=user.id).order_by(TrackedKeyword.created_at.desc()).limit(5).all()
    recent_analyses = SEOAnalysis.query.filter_by(user_id=user.id).order_by(SEOAnalysis.created_at.desc()).limit(5).all()
    
    return render_template('dashboard.html', 
                         user=user, 
                         limits=limits,
                         total_keywords=total_keywords,
                         total_analyses=total_analyses,
                         recent_keywords=recent_keywords,
                         recent_analyses=recent_analyses)

@app.route('/api/add-keyword', methods=['POST'])
@login_required
@limiter.limit("30 per hour")  # Limit keyword additions
def api_add_keyword():
    # Check usage limits
    if not current_user.can_use_feature('tracked_keywords'):
        limits = current_user.get_plan_limits()
        return jsonify({
            'error': f'Tracking limit reached. You can track up to {limits["tracked_keywords"]} keywords with your current plan.',
            'upgrade_required': True
        }), 429
    
    data = request.get_json()
    keyword = sanitize_input(data.get('keyword', '')).strip()
    domain = sanitize_input(data.get('domain', '')).strip()
    
    if not keyword or not domain:
        return jsonify({'error': 'Keyword and domain are required'}), 400
    
    # Clean domain
    domain = domain.replace('https://', '').replace('http://', '').replace('www.', '').strip('/')
    
    # Check if user can track more keywords
    if not current_user.can_track_more_keywords():
        limits = current_user.get_plan_limits()
        return jsonify({
            'error': f'Keyword limit reached. {current_user.get_plan_display_name()} plan allows {limits["tracked_keywords"]} keywords.',
            'upgrade_required': True
        }), 403
    
    # Check if already tracking this keyword for this domain for this user
    existing = TrackedKeyword.query.filter_by(keyword=keyword, domain=domain, user_id=current_user.id).first()
    if existing:
        return jsonify({'error': 'Already tracking this keyword for this domain'}), 400
    
    try:
        tracked_keyword = TrackedKeyword(keyword=keyword, domain=domain, user_id=current_user.id)
        db.session.add(tracked_keyword)
        db.session.commit()
        
        # Initial ranking check (mock for MVP)
        position = check_keyword_ranking(keyword, domain)
        
        ranking = Ranking(
            keyword_id=tracked_keyword.id,
            position=position,
            url=f"https://{domain}"
        )
        db.session.add(ranking)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'position': position,
            'keyword_id': tracked_keyword.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Database error: {str(e)}'}), 500

@app.route('/api/keywords')
@login_required
def api_get_keywords():
    """Get all tracked keywords with latest rankings for current user"""
    keywords = db.session.query(TrackedKeyword).filter_by(user_id=current_user.id).all()
    results = []
    
    for keyword in keywords:
        latest_ranking = db.session.query(Ranking).filter_by(
            keyword_id=keyword.id
        ).order_by(Ranking.checked_at.desc()).first()
        
        results.append({
            'id': keyword.id,
            'keyword': keyword.keyword,
            'domain': keyword.domain,
            'position': latest_ranking.position if latest_ranking else None,
            'last_checked': latest_ranking.checked_at.isoformat() if latest_ranking else None,
            'created_at': keyword.created_at.isoformat()
        })
    
    return jsonify({'keywords': results})

@app.route('/api/delete-keyword/<int:keyword_id>', methods=['DELETE'])
@login_required
def api_delete_keyword(keyword_id):
    """Delete a tracked keyword and its rankings for current user"""
    try:
        # Check if keyword belongs to current user
        keyword = TrackedKeyword.query.filter_by(id=keyword_id, user_id=current_user.id).first()
        if not keyword:
            return jsonify({'error': 'Keyword not found'}), 404
        
        # Delete rankings first
        Ranking.query.filter_by(keyword_id=keyword_id).delete()
        
        # Delete keyword
        db.session.delete(keyword)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

def check_keyword_ranking(keyword, domain):
    """Check keyword ranking (simplified mock version for MVP)"""
    # This is a mock implementation for MVP
    # In production, you would use:
    # - DataForSEO API
    # - ScrapingBee
    # - Custom SERP scraping (be careful with rate limits)
    
    try:
        # Mock ranking based on keyword characteristics
        keyword_lower = keyword.lower()
        domain_parts = domain.split('.')
        
        # Give better mock rankings for certain patterns
        if len(keyword.split()) >= 3:  # Long-tail keywords
            return random.randint(1, 15)
        elif any(word in keyword_lower for word in ['best', 'how to', 'guide', 'tutorial']):
            return random.randint(5, 25)
        elif domain_parts[0] in keyword_lower:  # Brand match
            return random.randint(1, 10)
        else:
            return random.randint(10, 50)
            
    except Exception as e:
        print(f"Error checking ranking: {e}")
        return None

# Initialize database tables when app starts
def init_db():
    with app.app_context():
        db.create_all()
        logger.info("Database tables created successfully")

# Initialize database on import (works with gunicorn)
try:
    init_db()
except Exception as e:
    logger.warning(f"Database initialization warning: {e}")

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=os.environ.get('FLASK_ENV') != 'production')