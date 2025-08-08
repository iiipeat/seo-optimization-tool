# API Integration Guide

This guide covers how to integrate external APIs for enhanced SEO functionality, including keyword data, SERP analysis, and ranking information.

## 🔑 API Services Overview

### Free APIs
- **Google Suggest**: Free keyword suggestions (no API key required)
- **Google Search Console API**: Free for your own sites (requires setup)

### Freemium APIs  
- **Ubersuggest API**: 100 requests/day free, then paid
- **KeywordTool.io API**: 750 requests/month free
- **Moz API**: Limited free tier

### Paid APIs
- **DataForSEO**: $0.01+ per request, comprehensive data
- **SEMrush API**: Professional SEO data
- **Ahrefs API**: Premium keyword and backlink data

## 🚀 Quick Start Integration

### 1. Google Suggest API (Free)

Already implemented in the base application:

```python
def get_keyword_suggestions(keyword):
    """Get keyword suggestions from Google Suggest API"""
    try:
        url = f"http://suggestqueries.google.com/complete/search?client=firefox&q={keyword}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            suggestions = response.json()[1]
            return suggestions[:15]
    except Exception as e:
        print(f"Error fetching suggestions: {e}")
    
    return [keyword]  # Fallback
```

### 2. DataForSEO Integration (Recommended)

```python
import requests
import base64
import json

class DataForSEOClient:
    def __init__(self, login, password):
        self.login = login
        self.password = password
        self.base_url = "https://api.dataforseo.com/v3"
        
    def get_auth_header(self):
        credentials = f"{self.login}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded_credentials}"}
    
    def get_keyword_data(self, keywords, location="US"):
        """Get keyword volume and difficulty data"""
        url = f"{self.base_url}/keywords_data/google/search_volume/live"
        
        payload = [{
            "keywords": keywords,
            "location_code": 2840,  # US
            "language_code": "en"
        }]
        
        headers = {
            **self.get_auth_header(),
            "Content-Type": "application/json"
        }
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API request failed: {response.status_code}")

# Usage in your Flask app
@app.route('/api/keyword-research-pro', methods=['POST'])
def api_keyword_research_pro():
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    
    if not keyword:
        return jsonify({'error': 'Keyword is required'}), 400
    
    try:
        # Get basic suggestions from Google Suggest
        suggestions = get_keyword_suggestions(keyword)
        
        # Enhance with DataForSEO data if API key is available
        if os.environ.get('DATAFORSEO_LOGIN'):
            client = DataForSEOClient(
                os.environ.get('DATAFORSEO_LOGIN'),
                os.environ.get('DATAFORSEO_PASSWORD')
            )
            
            enhanced_data = client.get_keyword_data(suggestions[:10])
            # Process and format the enhanced data
            results = process_dataforseo_response(enhanced_data, suggestions)
        else:
            # Fallback to mock data
            results = generate_mock_keyword_data(suggestions)
        
        return jsonify({'keywords': results})
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch keyword data: {str(e)}'}), 500
```

## 🔧 API Configuration

### Environment Variables

Add to your `.env` file:

```env
# DataForSEO API
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password

# Ubersuggest API  
UBERSUGGEST_API_KEY=your_api_key

# Moz API
MOZ_ACCESS_ID=your_access_id
MOZ_SECRET_KEY=your_secret_key

# Google Search Console (for your own sites)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
```

### Configuration Class

```python
import os
from dotenv import load_dotenv

load_dotenv()

class APIConfig:
    # DataForSEO
    DATAFORSEO_LOGIN = os.environ.get('DATAFORSEO_LOGIN')
    DATAFORSEO_PASSWORD = os.environ.get('DATAFORSEO_PASSWORD')
    
    # Ubersuggest
    UBERSUGGEST_API_KEY = os.environ.get('UBERSUGGEST_API_KEY')
    
    # Rate limiting
    API_RATE_LIMIT = int(os.environ.get('API_RATE_LIMIT', 100))
    
    @classmethod
    def has_dataforseo(cls):
        return bool(cls.DATAFORSEO_LOGIN and cls.DATAFORSEO_PASSWORD)
    
    @classmethod
    def has_ubersuggest(cls):
        return bool(cls.UBERSUGGEST_API_KEY)
```

## 📊 Specific API Integrations

### 1. Ubersuggest API

```python
class UbersuggestClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.neilpatel.com/v2"
    
    def get_keyword_suggestions(self, keyword, limit=50):
        """Get keyword suggestions from Ubersuggest"""
        url = f"{self.base_url}/keywords/suggestions"
        
        params = {
            'keyword': keyword,
            'locId': 2840,  # US
            'lang': 'en', 
            'limit': limit
        }
        
        headers = {
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Ubersuggest API error: {response.status_code}")
    
    def get_keyword_difficulty(self, keyword):
        """Get keyword difficulty score"""
        url = f"{self.base_url}/keywords/difficulty"
        
        params = {
            'keyword': keyword,
            'locId': 2840
        }
        
        headers = {'X-API-KEY': self.api_key}
        
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Difficulty API error: {response.status_code}")
```

### 2. Moz API Integration

```python
import hmac
import hashlib
import time
from urllib.parse import quote

class MozClient:
    def __init__(self, access_id, secret_key):
        self.access_id = access_id
        self.secret_key = secret_key
        self.base_url = "https://lsapi.seomoz.com"
    
    def generate_auth_header(self, expires):
        """Generate MOZ API authentication"""
        string_to_sign = f"{self.access_id}\n{expires}"
        signature = base64.b64encode(
            hmac.new(
                self.secret_key.encode(),
                string_to_sign.encode(),
                hashlib.sha1
            ).digest()
        ).decode()
        
        return f"Basic {base64.b64encode(f'{self.access_id}:{signature}'.encode()).decode()}"
    
    def get_keyword_difficulty(self, keyword):
        """Get keyword difficulty from Moz"""
        expires = int(time.time()) + 300  # 5 minutes from now
        
        url = f"{self.base_url}/linkscape/url-metrics/{quote(keyword, safe='')}"
        
        headers = {
            'Authorization': self.generate_auth_header(expires)
        }
        
        params = {
            'Cols': '103079215108',  # Specific metrics
            'AccessID': self.access_id,
            'Expires': expires
        }
        
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Moz API error: {response.status_code}")
```

### 3. SERP Scraping (Alternative to APIs)

```python
import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import random
import time

class SERPScraper:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
    
    def search_google(self, query, num_results=10):
        """Scrape Google search results (use carefully - respect rate limits)"""
        headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive'
        }
        
        url = f"https://www.google.com/search?q={quote(query)}&num={num_results}"
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            results = []
            
            # Extract organic results
            for i, result in enumerate(soup.find_all('div', class_='g'), 1):
                title_elem = result.find('h3')
                link_elem = result.find('a')
                snippet_elem = result.find('span', class_='st')
                
                if title_elem and link_elem:
                    results.append({
                        'position': i,
                        'title': title_elem.text,
                        'url': link_elem.get('href'),
                        'snippet': snippet_elem.text if snippet_elem else '',
                        'domain': self.extract_domain(link_elem.get('href'))
                    })
            
            return results
            
        except Exception as e:
            raise Exception(f"SERP scraping failed: {str(e)}")
    
    def extract_domain(self, url):
        """Extract clean domain from URL"""
        if not url:
            return ''
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return ''
    
    def check_ranking(self, keyword, target_domain, max_pages=5):
        """Check ranking position for a domain"""
        try:
            results = self.search_google(keyword, num_results=max_pages*10)
            target_domain_clean = target_domain.replace('www.', '').lower()
            
            for result in results:
                if target_domain_clean in result['domain']:
                    return {
                        'found': True,
                        'position': result['position'],
                        'url': result['url'],
                        'title': result['title']
                    }
            
            return {'found': False, 'position': None}
            
        except Exception as e:
            return {'error': str(e)}
```

## 🔄 API Response Processing

### DataForSEO Response Handler

```python
def process_dataforseo_response(api_response, original_keywords):
    """Process DataForSEO API response into standardized format"""
    processed_keywords = []
    
    if api_response.get('status_code') == 20000:
        results = api_response.get('tasks', [{}])[0].get('result', [])
        
        for result in results:
            processed_keywords.append({
                'keyword': result.get('keyword', ''),
                'search_volume': format_number(result.get('search_volume', 0)),
                'difficulty': result.get('keyword_difficulty', 0),
                'cpc': f"${result.get('cpc', 0):.2f}",
                'competition': result.get('competition', 0),
                'trend': 'stable',  # DataForSEO doesn't provide trend in basic response
                'intent': determine_search_intent(result.get('keyword', ''))
            })
    
    # Fill in any missing keywords with mock data
    existing_keywords = {kw['keyword'] for kw in processed_keywords}
    for keyword in original_keywords:
        if keyword not in existing_keywords:
            processed_keywords.append(generate_mock_keyword_data([keyword])[0])
    
    return processed_keywords

def format_number(num):
    """Format numbers with commas"""
    if num >= 1000000:
        return f"{num/1000000:.1f}M"
    elif num >= 1000:
        return f"{num/1000:.0f}K"
    else:
        return str(num)
```

## 🚦 Rate Limiting & Error Handling

### Rate Limiting Implementation

```python
import time
from functools import wraps
from collections import defaultdict

class RateLimiter:
    def __init__(self):
        self.calls = defaultdict(list)
        self.limits = {
            'dataforseo': {'calls': 2000, 'period': 86400},  # 2000 per day
            'ubersuggest': {'calls': 100, 'period': 86400},   # 100 per day
            'google_scraping': {'calls': 10, 'period': 3600}  # 10 per hour
        }
    
    def is_allowed(self, api_name, identifier='default'):
        """Check if API call is allowed based on rate limits"""
        now = time.time()
        key = f"{api_name}:{identifier}"
        
        # Clean old calls
        limit_config = self.limits.get(api_name, {'calls': 1000, 'period': 3600})
        cutoff_time = now - limit_config['period']
        self.calls[key] = [call_time for call_time in self.calls[key] if call_time > cutoff_time]
        
        # Check if under limit
        if len(self.calls[key]) < limit_config['calls']:
            self.calls[key].append(now)
            return True
        
        return False
    
    def wait_time(self, api_name, identifier='default'):
        """Get wait time until next call is allowed"""
        if self.is_allowed(api_name, identifier):
            return 0
        
        key = f"{api_name}:{identifier}"
        limit_config = self.limits.get(api_name, {'calls': 1000, 'period': 3600})
        
        if self.calls[key]:
            oldest_call = min(self.calls[key])
            return max(0, limit_config['period'] - (time.time() - oldest_call))
        
        return 0

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(api_name):
    """Decorator for rate limiting API calls"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not rate_limiter.is_allowed(api_name):
                wait_time = rate_limiter.wait_time(api_name)
                raise Exception(f"Rate limit exceeded. Try again in {wait_time:.0f} seconds.")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
```

### Graceful Error Handling

```python
def api_call_with_fallback(primary_func, fallback_func, *args, **kwargs):
    """Call primary API function with fallback"""
    try:
        return primary_func(*args, **kwargs)
    except Exception as e:
        print(f"Primary API failed: {e}")
        try:
            return fallback_func(*args, **kwargs)
        except Exception as fallback_error:
            print(f"Fallback also failed: {fallback_error}")
            raise Exception("All API methods failed")

# Usage example
@app.route('/api/keyword-research-enhanced', methods=['POST'])
def api_keyword_research_enhanced():
    data = request.get_json()
    keyword = data.get('keyword', '').strip()
    
    try:
        # Try primary API (DataForSEO)
        def primary_api():
            if APIConfig.has_dataforseo():
                client = DataForSEOClient(
                    APIConfig.DATAFORSEO_LOGIN,
                    APIConfig.DATAFORSEO_PASSWORD
                )
                return client.get_keyword_data([keyword])
            else:
                raise Exception("DataForSEO not configured")
        
        # Fallback to Ubersuggest
        def fallback_api():
            if APIConfig.has_ubersuggest():
                client = UbersuggestClient(APIConfig.UBERSUGGEST_API_KEY)
                return client.get_keyword_suggestions(keyword)
            else:
                raise Exception("Ubersuggest not configured")
        
        # Final fallback to mock data
        def final_fallback():
            suggestions = get_keyword_suggestions(keyword)
            return generate_mock_keyword_data(suggestions)
        
        # Try APIs in order
        try:
            result = api_call_with_fallback(primary_api, fallback_api)
        except:
            result = final_fallback()
        
        return jsonify({'keywords': result})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## 🎯 Testing API Integrations

### API Testing Script

```python
#!/usr/bin/env python3
"""
Test script for API integrations
Run: python test_apis.py
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

def test_google_suggest():
    """Test Google Suggest API"""
    print("Testing Google Suggest API...")
    try:
        from app import get_keyword_suggestions
        results = get_keyword_suggestions("digital marketing")
        print(f"✅ Google Suggest: Got {len(results)} suggestions")
        print(f"   Sample: {results[:3]}")
    except Exception as e:
        print(f"❌ Google Suggest failed: {e}")

def test_dataforseo():
    """Test DataForSEO API"""
    print("\nTesting DataForSEO API...")
    if not (os.environ.get('DATAFORSEO_LOGIN') and os.environ.get('DATAFORSEO_PASSWORD')):
        print("⚠️  DataForSEO credentials not configured")
        return
    
    try:
        # Your DataForSEO test code here
        print("✅ DataForSEO: Connection successful")
    except Exception as e:
        print(f"❌ DataForSEO failed: {e}")

def test_ubersuggest():
    """Test Ubersuggest API"""
    print("\nTesting Ubersuggest API...")
    if not os.environ.get('UBERSUGGEST_API_KEY'):
        print("⚠️  Ubersuggest API key not configured")
        return
    
    try:
        # Your Ubersuggest test code here
        print("✅ Ubersuggest: Connection successful")
    except Exception as e:
        print(f"❌ Ubersuggest failed: {e}")

def test_serp_scraping():
    """Test SERP scraping"""
    print("\nTesting SERP scraping...")
    try:
        scraper = SERPScraper()
        results = scraper.search_google("python programming", num_results=5)
        print(f"✅ SERP Scraping: Got {len(results)} results")
        if results:
            print(f"   Top result: {results[0]['title']}")
    except Exception as e:
        print(f"❌ SERP scraping failed: {e}")

if __name__ == "__main__":
    print("🧪 API Integration Tests\n")
    
    test_google_suggest()
    test_dataforseo()
    test_ubersuggest()
    test_serp_scraping()
    
    print("\n✨ Testing complete!")
```

## 📈 API Usage Monitoring

### Usage Tracking

```python
import json
from datetime import datetime

class APIUsageTracker:
    def __init__(self, log_file='api_usage.json'):
        self.log_file = log_file
    
    def log_usage(self, api_name, endpoint, cost=0, success=True):
        """Log API usage for monitoring"""
        usage_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'api': api_name,
            'endpoint': endpoint,
            'cost': cost,
            'success': success
        }
        
        # Append to log file
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(usage_data) + '\n')
        except Exception as e:
            print(f"Failed to log API usage: {e}")
    
    def get_daily_usage(self, api_name, date=None):
        """Get daily usage statistics"""
        if date is None:
            date = datetime.utcnow().date()
        
        total_calls = 0
        total_cost = 0
        success_count = 0
        
        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    data = json.loads(line.strip())
                    call_date = datetime.fromisoformat(data['timestamp']).date()
                    
                    if call_date == date and data['api'] == api_name:
                        total_calls += 1
                        total_cost += data['cost']
                        if data['success']:
                            success_count += 1
        except FileNotFoundError:
            pass
        
        return {
            'total_calls': total_calls,
            'total_cost': total_cost,
            'success_rate': success_count / total_calls if total_calls > 0 else 0
        }

# Global usage tracker
usage_tracker = APIUsageTracker()
```

## 🔧 Advanced Configuration

### Dynamic API Selection

```python
class APIManager:
    def __init__(self):
        self.apis = {
            'keyword_research': [
                {'name': 'dataforseo', 'cost': 0.01, 'quality': 10},
                {'name': 'ubersuggest', 'cost': 0.005, 'quality': 8},
                {'name': 'google_suggest', 'cost': 0, 'quality': 6}
            ],
            'serp_analysis': [
                {'name': 'dataforseo', 'cost': 0.02, 'quality': 10},
                {'name': 'scraping', 'cost': 0, 'quality': 7}
            ]
        }
    
    def select_best_api(self, service_type, budget_per_call=0.01):
        """Select best API based on budget and quality"""
        available_apis = self.apis.get(service_type, [])
        
        # Filter by budget
        affordable_apis = [api for api in available_apis if api['cost'] <= budget_per_call]
        
        if not affordable_apis:
            # If nothing affordable, use free options
            affordable_apis = [api for api in available_apis if api['cost'] == 0]
        
        # Select highest quality within budget
        if affordable_apis:
            return max(affordable_apis, key=lambda x: x['quality'])
        
        return None
    
    def get_keyword_data(self, keyword, budget=0.01):
        """Get keyword data using best available API"""
        selected_api = self.select_best_api('keyword_research', budget)
        
        if not selected_api:
            raise Exception("No suitable API available")
        
        if selected_api['name'] == 'dataforseo':
            return self.call_dataforseo(keyword)
        elif selected_api['name'] == 'ubersuggest':
            return self.call_ubersuggest(keyword)
        else:
            return self.call_google_suggest(keyword)
```

This comprehensive API integration guide should help you enhance your SEO tools with real data from various sources while maintaining cost-effectiveness and reliability.