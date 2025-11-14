from django.urls import path
from . import views

urlpatterns = [
    path('v1/health', views.health_check, name='health-check'),
    path('v1/stats', views.email_stats, name='email-stats'),
    path('v1/logs', views.email_logs, name='email-logs'),
    path('v1/rate-limit', views.rate_limit_info, name='rate-limit-info'),
]