from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User


def send_new_listing_to_admin(dog):
    """Notify admin when new dog listing is submitted"""
    admin_emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
    admin_emails = [email for email in admin_emails if email]
    
    if not admin_emails:
        return
    
    subject = f'New Dog Listing: {dog.name}'
    message = f"""
    New dog listing submitted for approval:
    
    - Name: {dog.name}
    - Breed: {dog.breed}
    - Age: {dog.age}
    - Location: {dog.location}
    - Price: रु{dog.price}
    - Listed by: {dog.lister.username if dog.lister else 'Unknown'}
    
    Review at: http://localhost:8000/admin/dog/dog/{dog.id}/change/
    
    Pethood
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, list(admin_emails), fail_silently=False)
    except Exception as e:
        print(f"Email error: {e}")


def send_listing_approved(dog):
    """Notify lister when their listing is approved"""
    if not dog.lister or not dog.lister.email:
        return
    
    subject = f'Your listing for {dog.name} is approved!'
    message = f"""
    Hi {dog.lister.username},
    
    Good news! Your dog listing has been approved and is now live.
    
    - Dog: {dog.name}
    - View at: http://localhost:8000/dogs/{dog.slug}/
    
    Best regards,
    Pethood Team
    """
    
    try:
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [dog.lister.email], fail_silently=False)
    except Exception as e:
        print(f"Email error: {e}")
