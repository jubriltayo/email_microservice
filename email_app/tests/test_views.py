import json
from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from email_app.models import EmailLog

class HealthCheckViewTest(TestCase):
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.client.get(reverse('health-check'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'healthy')
        self.assertEqual(data['data']['service'], 'email_service')

class EmailStatsViewTest(TestCase):
    def setUp(self):
        # Create test email logs
        EmailLog.objects.create(
            request_id='req1', user_id='user1', template_code='template1',
            recipient_email='test1@example.com', subject='Subject 1', body='Body 1',
            status='delivered'
        )
        EmailLog.objects.create(
            request_id='req2', user_id='user2', template_code='template2',
            recipient_email='test2@example.com', subject='Subject 2', body='Body 2',
            status='failed'
        )
        EmailLog.objects.create(
            request_id='req3', user_id='user3', template_code='template3',
            recipient_email='test3@example.com', subject='Subject 3', body='Body 3',
            status='pending'
        )
    
    def test_email_stats(self):
        """Test email statistics endpoint"""
        response = self.client.get(reverse('email-stats'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['total_emails'], 3)
        self.assertEqual(data['data']['delivered_emails'], 1)
        self.assertEqual(data['data']['failed_emails'], 1)
        self.assertEqual(data['data']['pending_emails'], 1)
        self.assertEqual(data['data']['success_rate'], 33.33)

class EmailLogsViewTest(TestCase):
    def setUp(self):
        # Create test email logs
        for i in range(5):
            EmailLog.objects.create(
                request_id=f'req{i}', user_id='user1', template_code='template1',
                recipient_email=f'test{i}@example.com', subject=f'Subject {i}',
                body=f'Body {i}', status='delivered'
            )
    
    def test_email_logs_list(self):
        """Test email logs listing"""
        response = self.client.get(reverse('email-logs'))
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 5)
    
    def test_email_logs_filter_by_user(self):
        """Test email logs filtering by user_id"""
        response = self.client.get(reverse('email-logs') + '?user_id=user1')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 5)
    
    def test_email_logs_filter_by_status(self):
        """Test email logs filtering by status"""
        response = self.client.get(reverse('email-logs') + '?status=delivered')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 5)

class RateLimitInfoViewTest(TestCase):
    @patch('email_app.utils.RateLimiter.get_rate_limit_info')
    def test_rate_limit_info(self, mock_get_info):
        """Test rate limit information endpoint with mocked RateLimiter"""
        # Mock the rate limit info to avoid Redis dependency
        mock_get_info.return_value = {
            'current_count': 5,
            'limit': 100,
            'remaining': 95
        }
        
        response = self.client.get(reverse('rate-limit-info') + '?user_id=test_user')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['current_count'], 5)
        self.assertEqual(data['data']['limit'], 100)
        self.assertEqual(data['data']['remaining'], 95)
    
    def test_rate_limit_info_missing_user_id(self):
        """Test rate limit info without user_id"""
        response = self.client.get(reverse('rate-limit-info'))
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        
        self.assertFalse(data['success'])
        self.assertIn('user_id parameter required', data['error'])
    
    @patch('email_app.utils.RateLimiter.get_rate_limit_info')
    def test_rate_limit_info_with_mock_error(self, mock_get_info):
        """Test rate limit info when RateLimiter has issues"""
        # Simulate Redis connection issue
        mock_get_info.side_effect = Exception("Redis connection failed")
        
        response = self.client.get(reverse('rate-limit-info') + '?user_id=test_user')
        
        # Should handle the error gracefully
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertFalse(data['success'])