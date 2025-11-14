import json
from unittest.mock import patch, Mock
from django.test import TestCase
from email_app.consumer import EmailConsumer
from email_app.models import EmailLog

class EmailConsumerTest(TestCase):
    def setUp(self):
        self.consumer = EmailConsumer()
        self.consumer.retry_counts = {}
    
    @patch('email_app.consumer.pika.BlockingConnection')
    def test_connect_success(self, mock_connection):
        """Test successful RabbitMQ connection"""
        mock_channel = Mock()
        mock_connection.return_value.channel.return_value = mock_channel
        
        # Mock the queue_declare and other channel methods
        mock_channel.queue_declare.return_value = None
        mock_channel.queue_bind.return_value = None
        mock_channel.basic_qos.return_value = None
        
        try:
            self.consumer.connect()
            connected = True
        except:
            connected = False
        
        self.assertTrue(connected)
    
    @patch('email_app.utils.HTTPClient.get_user_data')
    @patch('email_app.utils.HTTPClient.render_template')
    @patch('email_app.utils.EmailSender.send_email')
    def test_process_message_success(self, mock_send_email, mock_render_template, mock_get_user_data):
        """Test successful message processing"""
        # Mock dependencies
        mock_get_user_data.return_value = {
            'user_id': 'test_user',
            'email': 'test@example.com',
            'email_notifications': True
        }
        mock_render_template.return_value = {
            'rendered_subject': 'Welcome Test!',
            'rendered_body': 'Hello Test!'
        }
        mock_send_email.return_value = (True, None)
        
        # Mock channel and method
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 1
        
        # Test message
        test_message = {
            'request_id': 'test_req_001',
            'user_id': 'test_user',
            'template_code': 'welcome_email',
            'variables': {'name': 'Test'},
            'notification_type': 'email'
        }
        
        message_body = json.dumps(test_message)
        
        # Call process_message
        self.consumer.process_message(mock_channel, mock_method, None, message_body)
        
        # Verify email was sent
        mock_send_email.assert_called_once()
        
        # Verify email log was created
        email_log = EmailLog.objects.get(request_id='test_req_001')
        self.assertEqual(email_log.status, 'delivered')
    
    @patch('email_app.utils.HTTPClient.get_user_data')
    def test_process_message_user_not_found(self, mock_get_user_data):
        """Test message processing when user not found"""
        mock_get_user_data.return_value = None
        
        mock_channel = Mock()
        mock_method = Mock()
        mock_method.delivery_tag = 1
        
        test_message = {
            'request_id': 'test_req_002',
            'user_id': 'non_existent_user',
            'template_code': 'welcome_email',
            'variables': {'name': 'Test'}
        }
        
        message_body = json.dumps(test_message)
        
        self.consumer.process_message(mock_channel, mock_method, None, message_body)
        
        # Verify email log was created with failed status
        email_log = EmailLog.objects.get(request_id='test_req_002')
        self.assertEqual(email_log.status, 'failed')
        self.assertIn('Failed to get user data', email_log.error_message)
    
    def test_should_retry_logic(self):
        """Test retry logic"""
        delivery_tag = 123
        
        # First 3 retries should return True
        for i in range(3):
            self.assertTrue(self.consumer._should_retry(delivery_tag))
        
        # 4th retry should return False
        self.assertFalse(self.consumer._should_retry(delivery_tag))