from io import StringIO
from unittest.mock import patch, Mock
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError

class StartEmailConsumerCommandTest(TestCase):
    @patch('email_app.management.commands.start_email_consumer.EmailConsumer')
    def test_command_success(self, mock_consumer):
        """Test successful command execution"""
        mock_instance = Mock()
        mock_consumer.return_value = mock_instance
        
        # Mock keyboard interrupt to stop the infinite loop
        mock_instance.start_consuming.side_effect = KeyboardInterrupt
        
        out = StringIO()
        try:
            call_command('start_email_consumer', stdout=out)
        except SystemExit:
            pass
        
        self.assertIn('Starting Email Consumer', out.getvalue())
    
    @patch('email_app.management.commands.start_email_consumer.EmailConsumer')
    def test_command_error(self, mock_consumer):
        """Test command execution with error"""
        mock_instance = Mock()
        mock_consumer.return_value = mock_instance
        mock_instance.start_consuming.side_effect = Exception('Test error')
        
        out = StringIO()
        try:
            call_command('start_email_consumer', stdout=out)
        except SystemExit:
            pass
        
        self.assertIn('Email Consumer error', out.getvalue())