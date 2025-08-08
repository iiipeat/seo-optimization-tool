# SEO Tools - Free SEO Analysis Platform

A comprehensive SEO optimization website built with Flask, designed for solo developers and small businesses. This platform provides keyword research, on-page SEO analysis, and rank tracking capabilities - all for free.

## 🚀 Features

### Core Tools
- **Keyword Research Tool**: Discover profitable keywords with search volume and difficulty scores
- **On-Page SEO Checker**: Comprehensive website analysis with actionable recommendations  
- **Rank Tracker**: Monitor keyword rankings over time

### Key Benefits
- ✅ 100% Free to use
- ✅ No registration required
- ✅ Instant results
- ✅ Mobile-friendly interface
- ✅ Export functionality
- ✅ Privacy-focused (no data collection)

## 🛠 Technology Stack

- **Backend**: Flask (Python 3.11+)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Database**: SQLite (development) / PostgreSQL (production)
- **Deployment**: Railway.app / Heroku
- **APIs**: Google Suggest, BeautifulSoup for web scraping

## 📋 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd seo-website
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize database**
   ```bash
   python app.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Open in browser**
   ```
   http://localhost:5000
   ```

## 🚀 Deployment

### Option 1: Railway.app (Recommended)

1. **Install Railway CLI**
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. **Deploy**
   ```bash
   railway init
   railway up
   ```

3. **Add PostgreSQL**
   ```bash
   railway add postgresql
   ```

### Option 2: Heroku

1. **Install Heroku CLI and login**
   ```bash
   heroku login
   ```

2. **Create app and add database**
   ```bash
   heroku create your-seo-app-name
   heroku addons:create heroku-postgresql:hobby-dev
   ```

3. **Deploy**
   ```bash
   git push heroku main
   ```

## 📁 Project Structure

```
seo-website/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── Procfile                   # Deployment configuration
├── runtime.txt                # Python version
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── SEO_WEBSITE_DEVELOPMENT_GUIDE.md  # Comprehensive development guide
├── static/
│   ├── css/
│   │   └── style.css          # Custom CSS styles
│   └── js/
│       └── main.js            # JavaScript functionality
├── templates/
│   ├── base.html              # Base template
│   ├── index.html             # Homepage
│   ├── keyword_research.html  # Keyword research tool
│   ├── seo_checker.html       # SEO analysis tool
│   └── rank_tracker.html      # Rank tracking tool
├── BACKEND_API_AGENT.md       # Backend development guide
├── SEO_ANALYSIS_AGENT.md      # SEO analysis guide
└── FRONTEND_AGENT.md          # Frontend development guide
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///seo_tool.db
DEBUG=True
```

### Production Settings

For production deployment:

```env
FLASK_ENV=production
SECRET_KEY=your-secure-secret-key
DATABASE_URL=postgresql://user:password@host:port/database
DEBUG=False
```

## 🧪 Testing

### Manual Testing

1. **Keyword Research**
   - Enter a keyword (e.g., "digital marketing")
   - Verify suggestions appear
   - Check volume and difficulty scores

2. **SEO Checker**
   - Enter a URL (e.g., "https://example.com")
   - Verify analysis completes
   - Check recommendations are actionable

3. **Rank Tracker**
   - Add a keyword and domain
   - Verify tracking is saved
   - Check ranking position appears

### Automated Testing

```bash
# Run tests (when implemented)
python -m pytest tests/
```

## 🔍 API Documentation

### Keyword Research API

```http
POST /api/keyword-research
Content-Type: application/json

{
  "keyword": "digital marketing"
}
```

**Response:**
```json
{
  "keywords": [
    {
      "keyword": "digital marketing",
      "search_volume": "5,000",
      "difficulty": 45,
      "cpc": "$2.50",
      "trend": "stable"
    }
  ]
}
```

### SEO Analysis API

```http
POST /api/seo-analysis
Content-Type: application/json

{
  "url": "https://example.com"
}
```

**Response:**
```json
{
  "url": "https://example.com",
  "title": "Example Domain",
  "title_length": 14,
  "meta_description": "Example description",
  "word_count": 350,
  "score": 75,
  "issues": ["Title too short"],
  "recommendations": ["Expand title to 30-60 characters"]
}
```

### Rank Tracking API

```http
POST /api/add-keyword
Content-Type: application/json

{
  "keyword": "best laptops",
  "domain": "example.com"
}
```

**Response:**
```json
{
  "success": true,
  "position": 15,
  "keyword_id": 1
}
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
5. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
6. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 for Python code
- Use semantic HTML and accessible markup
- Test on multiple browsers and devices
- Document new features and API endpoints
- Keep commits small and focused

## 📚 Resources

### Documentation
- [SEO Website Development Guide](SEO_WEBSITE_DEVELOPMENT_GUIDE.md) - Comprehensive development guide
- [Backend API Agent](BACKEND_API_AGENT.md) - Backend development guidelines
- [SEO Analysis Agent](SEO_ANALYSIS_AGENT.md) - SEO analysis implementation
- [Frontend Agent](FRONTEND_AGENT.md) - Frontend development guidelines

### External APIs
- [Google Suggest API](http://suggestqueries.google.com/complete/search) - Free keyword suggestions
- [Ubersuggest API](https://neilpatel.com/ubersuggest/) - Keyword data (freemium)
- [DataForSEO](https://dataforseo.com/) - Comprehensive SEO data (paid)

### Tools & Services
- [Railway.app](https://railway.app/) - Deployment platform
- [Bootstrap 5](https://getbootstrap.com/) - CSS framework
- [Bootstrap Icons](https://icons.getbootstrap.com/) - Icon library

## 🔒 Security

### Best Practices Implemented

- Input validation and sanitization
- XSS protection
- CSRF protection (add Flask-WTF for forms)
- Rate limiting (implement as needed)
- Secure headers

### Reporting Security Issues

Please report security vulnerabilities to [your-email@domain.com]. Do not create public issues for security vulnerabilities.

## 📊 Performance

### Optimization Features

- Caching of analysis results
- Lazy loading of images
- Minified CSS and JavaScript
- Database query optimization
- CDN for static assets

### Monitoring

Consider adding:
- Google Analytics for usage tracking
- Sentry for error monitoring
- Performance monitoring tools

## 💰 Cost Analysis

### Free Tier Resources

| Service | Free Allowance | Monthly Cost |
|---------|---------------|--------------|
| Railway.app | 500 hours | $0 |
| PostgreSQL | 1GB | $0 |
| **Total** | | **$0-1/month** |

### Scaling Costs

As you grow:
- Railway Pro: $5/month
- PostgreSQL: $5/month  
- Domain: $12/year
- **Total: ~$11/month**

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
```bash
# Check DATABASE_URL environment variable
echo $DATABASE_URL

# Recreate database
rm seo_tool.db
python app.py
```

**Import Errors**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**Port Already in Use**
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9
```

### Debug Mode

Enable debug mode for development:
```python
app.run(debug=True)
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Bootstrap team for the excellent CSS framework
- Flask community for the micro-framework
- All contributors who help improve this project

## 📞 Support

- **Documentation**: Check the guides in this repository
- **Issues**: Create a GitHub issue for bugs or feature requests
- **Discussions**: Use GitHub Discussions for questions

---

**Built with ❤️ for the SEO community**

*Happy optimizing! 🚀*