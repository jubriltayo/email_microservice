import json
import logging
import pika
import time
import uuid
from django.conf import settings
from django.utils import timezone
from .models import EmailLog
from .utils import HTTPClient, EmailSender, CircuitBreaker, RateLimiter

logger = logging.getLogger(__name__)

class EmailConsumer:
    """Consumes messages from RabbitMQ and processes emails"""
    
    def __init__(self):
        self.connection = None
        self.channel = None
        self.circuit_breaker = CircuitBreaker(
            name="EmailService",
            failure_threshold=3,
            recovery_timeout=30
        )
        self.retry_counts = {}
    
    def connect(self):
        """Connect to RabbitMQ with retry logic"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.connection = pika.BlockingConnection(
                    pika.URLParameters(settings.RABBITMQ_URL)
                )
                self.channel = self.connection.channel()
                
                self.channel.exchange_declare(
                    exchange='notifications.direct',
                    exchange_type='direct',
                    durable=True
                )
                
                self.channel.queue_declare(
                    queue='email.queue',
                    durable=True,
                    arguments={
                        'x-dead-letter-exchange': 'dlx.notifications',
                        'x-dead-letter-routing-key': 'dl.email.queue',
                        'x-max-priority': 10
                    }     
                )
                self.channel.queue_declare(
                    queue='failed.queue',
                    durable=True
                )
                
                self.channel.queue_bind(
                    exchange='notifications.direct',
                    queue='email.queue',
                    routing_key='email'
                )
                
                self.channel.basic_qos(prefetch_count=1)
                
                logger.info("Connected to RabbitMQ successfully")
                return
                
            except Exception as e:
                logger.error(f"Failed to connect to RabbitMQ (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    raise
    
    def process_message(self, ch, method, properties, body):
        """Process a single message from the queue"""
        delivery_tag = method.delivery_tag
        message = None
        
        try:
            message = json.loads(body)
            request_id = message.get('request_id', str(uuid.uuid4()))
            user_id = message.get('user_id')
            
            logger.info(f"Processing email message: {request_id}")
            
            # Check rate limit
            if not RateLimiter.check_rate_limit(user_id, 'email'):
                error_msg = "Rate limit exceeded for user"
                self._handle_failure(None, error_msg, request_id, delivery_tag, ch, message)
                return
            
            # Check circuit breaker
            if not self.circuit_breaker.can_execute():
                error_msg = "Circuit breaker is OPEN - Email service unavailable"
                self._handle_failure(None, error_msg, request_id, delivery_tag, ch, message)
                return
            
            # Validate required fields
            required_fields = ['user_id', 'template_code', 'variables']
            for field in required_fields:
                if field not in message:
                    error_msg = f"Missing required field: {field}"
                    self._handle_failure(None, error_msg, request_id, delivery_tag, ch, message)
                    return
            
            # Create email log entry
            email_log = EmailLog.objects.create(
                request_id=request_id,
                user_id=user_id,
                template_code=message['template_code'],
                status='pending'
            )
            
            # Get user data
            user_data = HTTPClient.get_user_data(user_id)
            if not user_data:
                error_msg = "Failed to get user data"
                self._handle_failure(email_log, error_msg, request_id, delivery_tag, ch, message)
                return
            
            # Check user preferences
            if not user_data.get('email_notifications', True):
                logger.info(f"User {user_id} has disabled email notifications")
                email_log.status = 'failed'
                email_log.error_message = 'User disabled email notifications'
                email_log.save()
                HTTPClient.update_notification_status(request_id, 'failed', 'User disabled email notifications')
                ch.basic_ack(delivery_tag=delivery_tag)
                return
            
            recipient_email = user_data.get('email')
            if not recipient_email:
                error_msg = "User has no email address"
                self._handle_failure(email_log, error_msg, request_id, delivery_tag, ch, message)
                return
            
            # Render template
            template_data = HTTPClient.render_template(
                message['template_code'],
                message.get('language', 'en'),
                message['variables']
            )
            if not template_data:
                error_msg = "Failed to render email template"
                self._handle_failure(email_log, error_msg, request_id, delivery_tag, ch, message)
                return
            
            # Send email with retry
            success, error = self._send_with_retry(
                recipient_email=recipient_email,
                subject=template_data['rendered_subject'],
                body=template_data['rendered_body']
            )
            
            # Update status
            if success:
                email_log.status = 'delivered'
                email_log.recipient_email = recipient_email
                email_log.subject = template_data['rendered_subject']
                email_log.body = template_data['rendered_body']
                email_log.sent_at = timezone.now()
                email_log.save()
                
                HTTPClient.update_notification_status(request_id, 'delivered')
                self.circuit_breaker.record_success()
                logger.info(f"Email sent successfully: {request_id}")
                
                ch.basic_ack(delivery_tag=delivery_tag)
            else:
                self._handle_failure(email_log, error, request_id, delivery_tag, ch, message)
            
        except Exception as e:
            logger.error(f"Error processing email message: {e}")
            self.circuit_breaker.record_failure()
            
            # Check if we should retry
            if message and self._should_retry(delivery_tag):
                logger.info(f"Retrying message {delivery_tag}")
                ch.basic_nack(delivery_tag=delivery_tag, requeue=True)
            else:
                if message:
                    self._send_to_dlq(message, str(e))
                ch.basic_ack(delivery_tag=delivery_tag)
    
    def _send_with_retry(self, recipient_email, subject, body, html_body=None):
        """Send email with retry logic and exponential backoff"""
        for attempt in range(3):
            try:
                success, error = EmailSender.send_email(
                    recipient_email, subject, body, html_body
                )
                
                if success:
                    return True, None
                
                if attempt < 2:
                    sleep_time = (2 ** attempt)
                    logger.info(f"Email attempt {attempt + 1} failed, retrying in {sleep_time}s")
                    time.sleep(sleep_time)
                    
            except Exception as e:
                error = str(e)
                if attempt < 2:
                    sleep_time = (2 ** attempt)
                    logger.info(f"Email attempt {attempt + 1} failed with exception, retrying in {sleep_time}s")
                    time.sleep(sleep_time)
        
        return False, error or "All retry attempts failed"
    
    def _should_retry(self, delivery_tag):
        """Simple retry logic with max 3 retries"""
        if delivery_tag not in self.retry_counts:
            self.retry_counts[delivery_tag] = 0
        
        if self.retry_counts[delivery_tag] < 3:
            self.retry_counts[delivery_tag] += 1
            return True
        else:
            # Clean up old retry counts to prevent memory leaks
            if len(self.retry_counts) > 1000:
                self.retry_counts.clear()
            return False
    
    def _handle_failure(self, email_log, error_message, request_id, delivery_tag, ch, message=None):
        """Handle email sending failure"""
        if email_log:
            email_log.status = 'failed'
            email_log.error_message = error_message
            email_log.save()
        
        HTTPClient.update_notification_status(request_id, 'failed', error_message)
        self.circuit_breaker.record_failure()
        logger.error(f"Email failed: {request_id} - {error_message}")
        
        # Move to DLQ if permanent failure
        if message and any(term in error_message.lower() for term in ['permanent', 'disabled', 'no email']):
            self._send_to_dlq(message, error_message)
        
        ch.basic_ack(delivery_tag=delivery_tag)
    
    def _send_to_dlq(self, message, error):
        """Send failed message to dead letter queue"""
        try:
            connection = pika.BlockingConnection(
                pika.URLParameters(settings.RABBITMQ_URL)
            )
            channel = connection.channel()
            
            dlq_message = {
                'original_message': message,
                'error': error,
                'failed_at': timezone.now().isoformat(),
                'service': 'email_service'
            }
            
            channel.basic_publish(
                exchange='',
                routing_key='failed.queue',
                body=json.dumps(dlq_message),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            
            connection.close()
            logger.info(f"Message sent to DLQ: {message.get('request_id', 'unknown')}")
            
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
    
    def start_consuming(self):
        """Start consuming messages from the queue"""
        try:
            self.connect()
            
            self.channel.basic_consume(
                queue='email.queue',
                on_message_callback=self.process_message,
                auto_ack=False
            )
            
            logger.info("Email Consumer started. Waiting for messages...")
            self.channel.start_consuming()
            
        except Exception as e:
            logger.error(f"Email Consumer error: {e}")
            if self.connection:
                self.connection.close()
    
    def stop_consuming(self):
        """Stop the consumer"""
        if self.connection and not self.connection.is_closed:
            self.connection.close()