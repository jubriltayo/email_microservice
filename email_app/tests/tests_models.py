from django.test import TestCase
from django.utils import timezone
from email_app.models import EmailLog

class EmailLogModelTest(TestCase):
    def setUp(self):
        self.email_log = EmailLog.objects.create(
            request_id='test_request_123',
            user_id='test_user_001',
            template_code='welcome_email',
            recipient_email='test@example.com',
            subject='Test Subject',
            body='Test Body',
            status='pending'
        )
    
    def test_email_log_creation(self):
        """Test EmailLog model creation"""
        self.assertEqual(self.email_log.request_id, 'test_request_123')
        self.assertEqual(self.email_log.user_id, 'test_user_001')
        self.assertEqual(self.email_log.status, 'pending')
        self.assertEqual(self.email_log.recipient_email, 'test@example.com')
    
    def test_email_log_str_representation(self):
        """Test string representation of EmailLog"""
        expected_str = f"Email to test@example.com - pending"
        self.assertEqual(str(self.email_log), expected_str)
    
    def test_email_log_default_values(self):
        """Test EmailLog default values"""
        new_log = EmailLog.objects.create(
            request_id='test_request_456',
            user_id='test_user_002',
            template_code='welcome_email',
            recipient_email='test2@example.com',
            subject='Test Subject 2',
            body='Test Body 2'
        )
        self.assertEqual(new_log.status, 'pending')
        self.assertIsNone(new_log.error_message)
        self.assertIsNone(new_log.sent_at)
    
    def test_email_log_status_choices(self):
        """Test EmailLog status choices"""
        valid_statuses = ['pending', 'delivered', 'failed']
        for status in valid_statuses:
            self.email_log.status = status
            self.email_log.save()
            self.assertEqual(self.email_log.status, status)