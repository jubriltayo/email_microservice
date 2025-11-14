import requests
import logging
import time
from django.conf import settings
from django.core.cache import cache
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.core.exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

class HTTPClient:
    """HTTP client for calling external services with Redis caching"""
    
    @staticmethod
    def _make_request(method, url, json_data=None, timeout=10):
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-Internal-Secret': settings.SERVICE_TOKEN,
                'X-Service-Name': 'email_service'
            }
            
            logger.info(f"Making {method} request to: {url}")
            
            response = requests.request(
                method=method,
                url=url,
                json=json_data,
                headers=headers,
                timeout=timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Request successful: {url}")
                return result.get('data')
            elif response.status_code == 401:
                logger.error(f"Authentication failed for {url}. Check SERVICE_TOKEN configuration.")
                logger.error(f"Response: {response.text}")
                return None
            else:
                logger.error(f"Service call failed: {url} - Status: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Service call timeout: {url}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"Service connection error: {url}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Service call error: {url} - {e}")
            return None
    
    @staticmethod
    def get_user_data(user_id):
        """Get user data from User Service with Redis caching"""
        cache_key = f"user_preferences:{user_id}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            logger.info(f"User cache hit: {user_id}")
            return cached_data
        
        logger.info(f"Fetching user data: {user_id}")
        user_data = HTTPClient._make_request(
            'GET', 
            f"{settings.USER_SERVICE_URL}/api/v1/service/users/{user_id}"
        )
        
        if user_data:
            cache.set(cache_key, user_data, settings.USER_PREFERENCES_CACHE_TIMEOUT)
        
        return user_data
    
    @staticmethod
    def render_template(template_code, language, variables):
        """Render template from Template Service"""
        logger.info(f"Rendering template: {template_code}")
        return HTTPClient._make_request(
            'POST',
            f"{settings.TEMPLATE_SERVICE_URL}/api/v1/service/templates/render",
            {
                'template_code': template_code,
                'language': language,
                'variables': variables
            }
        )
    
    @staticmethod
    def update_notification_status(notification_id, status, error=None):
        """Update notification status via service endpoint"""
        logger.info(f"Updating notification status: {notification_id} -> {status}")
        return HTTPClient._make_request(
            'POST',
            # f"{settings.API_GATEWAY_URL}/api/v1/service/notification-status",
            f"{settings.API_GATEWAY_URL}/api/v1/internal/email/status",
            {
                'notification_id': notification_id,
                'status': status,
                'error': error
            }
        )

class EmailSender:
    """Handles actual email sending"""
    
    @staticmethod
    def send_email(recipient_email, subject, body, html_body=None):
        """Send an email using Django's email backend"""
        try:
            if not all([settings.EMAIL_HOST, settings.EMAIL_PORT, settings.EMAIL_HOST_USER]):
                raise ImproperlyConfigured("Email settings are not properly configured")
            
            logger.info(f"Attempting to send email to: {recipient_email}")
            
            if html_body:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient_email],
                )
                email.attach_alternative(html_body, "text/html")
            else:
                email = EmailMessage(
                    subject=subject,
                    body=body,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[recipient_email],
                )
            
            result = email.send(fail_silently=False)
            
            logger.info(f"Email sent successfully to: {recipient_email}")
            return True, None
            
        except Exception as e:
            error_msg = f"Email sending failed to {recipient_email}: {str(e)}"
            logger.error(error_msg)
            return False, str(e)

class CircuitBreaker:
    """Circuit breaker pattern implementation"""
    
    def __init__(self, name, failure_threshold=3, recovery_timeout=30):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self):
        """Check if request can be executed based on circuit state"""
        if self.state == 'CLOSED':
            return True
        
        elif self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                logger.info(f"Circuit breaker '{self.name}' -> HALF_OPEN")
                return True
            else:
                logger.warning(f"Circuit breaker '{self.name}' is OPEN - rejecting request")
                return False
        
        elif self.state == 'HALF_OPEN':
            return True
    
    def record_success(self):
        """Record a successful execution"""
        if self.state == 'HALF_OPEN':
            self.state = 'CLOSED'
            self.failure_count = 0
            logger.info(f"Circuit breaker '{self.name}' -> CLOSED (recovered)")
        elif self.state == 'CLOSED':
            if self.failure_count > 0:
                self.failure_count = max(0, self.failure_count - 1)
    
    def record_failure(self):
        """Record a failed execution"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        logger.warning(f"Circuit breaker '{self.name}' failure #{self.failure_count}")
        
        if self.state == 'HALF_OPEN':
            self.state = 'OPEN'
            logger.warning(f"Circuit breaker '{self.name}' -> OPEN (still failing)")
        
        elif self.state == 'CLOSED' and self.failure_count >= self.failure_threshold:
            self.state = 'OPEN'
            logger.error(f"Circuit breaker '{self.name}' -> OPEN (threshold reached)")

class RateLimiter:
    """Rate limiting with Redis"""
    
    @staticmethod
    def check_rate_limit(user_id, notification_type='email'):
        """Check if user has exceeded rate limit"""
        current_hour = int(time.time() // 3600)
        rate_limit_key = f"rate_limit:{user_id}:{notification_type}:{current_hour}"
        
        current_count = cache.get(rate_limit_key, 0)
        
        if current_count >= settings.EMAIL_RATE_LIMIT:
            logger.warning(f"Rate limit exceeded for user: {user_id}")
            return False
        
        cache.set(rate_limit_key, current_count + 1, settings.RATE_LIMIT_CACHE_TIMEOUT)
        return True
    
    @staticmethod
    def get_rate_limit_info(user_id, notification_type='email'):
        """Get current rate limit usage"""
        current_hour = int(time.time() // 3600)
        rate_limit_key = f"rate_limit:{user_id}:{notification_type}:{current_hour}"
        
        current_count = cache.get(rate_limit_key, 0)
        return {
            'current_count': current_count,
            'limit': settings.EMAIL_RATE_LIMIT,
            'remaining': max(0, settings.EMAIL_RATE_LIMIT - current_count)
        }