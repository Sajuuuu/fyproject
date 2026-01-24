from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
from django.template.loader import render_to_string


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


def send_listing_approved(dog, admin_message=''):
    """Notify lister when their listing is approved with HTML email"""
    if not dog.lister or not dog.lister.email:
        return
    
    subject = f'Your Dog Listing "{dog.name}" has been Approved!'
    
    # Plain text fallback
    text_content = f"""
Hi {dog.lister.first_name or dog.lister.username},

Great news! Your dog listing has been reviewed and approved by our team. It is now live on Pethood and visible to potential adopters.

Dog Details:
- Name: {dog.name}
- Breed: {dog.breed}
- Age: {dog.age} months
- Gender: {dog.get_gender_display()}
- Location: {dog.location}

{admin_message if admin_message else ''}

View your listing: http://localhost:8000/dogs/{dog.slug}/

Thank you for helping dogs find their forever homes!

Best regards,
The Pethood Team
    """
    
    # HTML content
    context = {
        'dog': dog,
        'admin_message': admin_message,
        'site_url': 'http://localhost:8000',
    }
    html_content = render_to_string('emails/dog_approval.html', context)
    
    try:
        # Create email with both plain text and HTML versions
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[dog.lister.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Email error: {e}")
