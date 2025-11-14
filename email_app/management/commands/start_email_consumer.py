from django.core.management.base import BaseCommand
from email_app.consumer import EmailConsumer
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Start the Email Service RabbitMQ consumer'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Email Consumer...')
        )
        
        consumer = EmailConsumer()
        
        try:
            consumer.start_consuming()
        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING('Stopping Email Consumer...')
            )
            consumer.stop_consuming()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Email Consumer error: {e}')
            )
            logger.error(f"Email Consumer failed: {e}")