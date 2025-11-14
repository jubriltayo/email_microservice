from django.db import models

class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ]
    
    request_id = models.CharField(max_length=100, unique=True)
    user_id = models.CharField(max_length=100)
    template_code = models.CharField(max_length=100)
    recipient_email = models.EmailField()
    subject = models.TextField()
    body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_logs'
        indexes = [
            models.Index(fields=['request_id']),
            models.Index(fields=['user_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Email to {self.recipient_email} - {self.status}"