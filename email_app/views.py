from rest_framework.decorators import api_view
from django.http import JsonResponse
from django.utils import timezone
from .models import EmailLog
from .utils import RateLimiter
import logging

logger = logging.getLogger(__name__)

def success_response(data=None, message="Success", status=200):
    return JsonResponse({
        'success': True,
        'data': data,
        'message': message
    }, status=status)

def error_response(error="Error", message="Failed", status=400):
    return JsonResponse({
        'success': False,
        'error': error,
        'message': message
    }, status=status)

@api_view(['GET'])
def health_check(request):
    """Health check endpoint"""
    try:
        # Test database connection
        EmailLog.objects.count()
        
        health_data = {
            'status': 'healthy',
            'service': 'email_service',
            'timestamp': timezone.now().isoformat()
        }
        
        return success_response(
            data=health_data,
            message="Email service is healthy"
        )
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return error_response(
            error=str(e),
            message="Service health check failed",
            status=503
        )

@api_view(['GET'])
def email_stats(request):
    """Get email statistics"""
    try:
        total_emails = EmailLog.objects.count()
        delivered_emails = EmailLog.objects.filter(status='delivered').count()
        failed_emails = EmailLog.objects.filter(status='failed').count()
        pending_emails = EmailLog.objects.filter(status='pending').count()
        
        success_rate = 0
        if total_emails > 0:
            success_rate = round((delivered_emails / total_emails) * 100, 2)
        
        stats = {
            'total_emails': total_emails,
            'delivered_emails': delivered_emails,
            'failed_emails': failed_emails,
            'pending_emails': pending_emails,
            'success_rate': success_rate,
        }
        
        return success_response(
            data=stats,
            message="Email statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting email stats: {e}")
        return error_response(
            error=str(e),
            message="Failed to retrieve email statistics",
            status=500
        )

@api_view(['GET'])
def email_logs(request):
    """Get email logs with filtering"""
    try:
        user_id = request.GET.get('user_id')
        status = request.GET.get('status')
        limit = int(request.GET.get('limit', 100))
        
        logs = EmailLog.objects.all().order_by('-created_at')
        
        if user_id:
            logs = logs.filter(user_id=user_id)
        if status:
            logs = logs.filter(status=status)
        
        logs = logs[:limit]
        
        log_data = []
        for log in logs:
            log_data.append({
                'request_id': log.request_id,
                'user_id': log.user_id,
                'recipient_email': log.recipient_email,
                'template_code': log.template_code,
                'status': log.status,
                'error_message': log.error_message,
                'sent_at': log.sent_at.isoformat() if log.sent_at else None,
                'created_at': log.created_at.isoformat()
            })
        
        return success_response(
            data=log_data,
            message="Email logs retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting email logs: {e}")
        return error_response(
            error=str(e),
            message="Failed to retrieve email logs",
            status=500
        )

@api_view(['GET'])
def rate_limit_info(request):
    """Get rate limit information for a user"""
    try:
        user_id = request.GET.get('user_id')
        if not user_id:
            return error_response(
                error="user_id parameter required",
                message="Missing user_id parameter",
                status=400
            )
        
        limit_info = RateLimiter.get_rate_limit_info(user_id, 'email')
        
        return success_response(
            data=limit_info,
            message="Rate limit information retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting rate limit info: {e}")
        return error_response(
            error=str(e),
            message="Failed to retrieve rate limit information",
            status=500
        )