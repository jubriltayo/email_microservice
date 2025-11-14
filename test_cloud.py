import os
import django
import redis
import pika
import ssl

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

def test_redis_cloud():
    """Test Redis Cloud without SSL"""
    try:
        print("🧪 Testing Redis Cloud (Non-SSL)...")
        r = redis.Redis(
            host='redis-10065.c246.us-east-1-4.ec2.cloud.redislabs.com',
            port=10065,
            password='LTLZrczgLNq4PQeVZI01H93XFzK4ascl',
            ssl=False,
            socket_connect_timeout=10,
            socket_timeout=10
        )
        r.ping()
        r.set('redis_test', 'success', ex=10)
        result = r.get('redis_test')
        print("✅ Redis Cloud: Connected and operational!")
        return True
    except Exception as e:
        print(f"❌ Redis Cloud failed: {e}")
        return False

def test_rabbitmq_cloud():
    """Test RabbitMQ Cloud with SSL"""
    try:
        print("🧪 Testing RabbitMQ Cloud (SSL)...")
        
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        url_params = pika.URLParameters('amqps://pxkefxtc:013yLE9kxuZ-6K0sKdjhUXrPs_Ix7z1C@hawk.rmq.cloudamqp.com/pxkefxtc')
        url_params.ssl_options = pika.SSLOptions(ssl_context)
        
        connection = pika.BlockingConnection(url_params)
        channel = connection.channel()
        
        # Test queue operations
        channel.queue_declare(queue='test_queue', durable=True)
        channel.queue_delete(queue='test_queue')
        
        connection.close()
        print("✅ RabbitMQ Cloud: Connected and operational!")
        return True
    except Exception as e:
        print(f"❌ RabbitMQ Cloud failed: {e}")
        return False

def test_django_integration():
    """Test Django with both services"""
    try:
        print("🧪 Testing Django integration...")
        from django.core.cache import cache
        
        # Test Redis via Django
        cache.set('django_cloud_test', 'success', 60)
        result = cache.get('django_cloud_test')
        
        if result == 'success':
            print("✅ Django Redis integration: Working!")
            return True
        else:
            print(f"❌ Django Redis integration: Unexpected result: {result}")
            return False
    except Exception as e:
        print(f"❌ Django integration failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing FULL CLOUD INFRASTRUCTURE")
    print("=" * 50)
    
    redis_ok = test_redis_cloud()
    print()
    rabbitmq_ok = test_rabbitmq_cloud() 
    print()
    django_ok = test_django_integration()
    print()
    print("=" * 50)
    
    if redis_ok and rabbitmq_ok and django_ok:
        print("🎉 FULL CLOUD MIGRATION SUCCESSFUL! 🎉")
        print("   Both Redis and RabbitMQ are now in the cloud!")
        print("   Your microservices architecture is fully cloud-based! 🚀")
    else:
        print("⚠️  Some services need attention")