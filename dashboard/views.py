from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Sum, Q
from shop.models import Product, Order, OrderItem, Size
from dog.models import Dog, DogImage
from dog.emails import send_listing_approved
from decimal import Decimal

# Context processor for notification counts
def get_notification_counts():
    """Get counts for pending items to show in sidebar"""
    pending_dogs = Dog.objects.filter(is_approved=False).count()
    pending_orders = Order.objects.filter(status='pending').count()
    return {
        'pending_dogs_count': pending_dogs,
        'pending_orders_count': pending_orders,
    }

# Admin Dashboard Home
@staff_member_required
def dashboard_home(request):
    """Main admin dashboard with statistics"""
    # Get statistics
    total_products = Product.objects.count()
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending').count()
    total_users = User.objects.count()
    total_dogs = Dog.objects.count()
    pending_dogs = Dog.objects.filter(is_approved=False).count()
    
    # Recent orders
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    
    # Revenue statistics
    total_revenue = Order.objects.exclude(status='cancelled').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_users': total_users,
        'total_dogs': total_dogs,
        'pending_dogs': pending_dogs,
        'recent_orders': recent_orders,
        'total_revenue': total_revenue,
        **get_notification_counts(),
    }
    return render(request, 'dashboard/home.html', context)


# ==================== PRODUCT MANAGEMENT ====================

@staff_member_required
def product_list(request):
    """List all products with search and filter"""
    query = request.GET.get('q', '')
    category = request.GET.get('category', '')
    
    products = Product.objects.all()
    
    if query:
        products = products.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )
    
    if category:
        products = products.filter(category=category)
    
    products = products.order_by('-id')
    
    context = {
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'query': query,
        'selected_category': category,
        **get_notification_counts(),
    }
    return render(request, 'dashboard/product_list.html', context)


@staff_member_required
def product_add(request):
    """Add new product"""
    if request.method == 'POST':
        try:
            product = Product.objects.create(
                name=request.POST.get('name'),
                category=request.POST.get('category'),
                price=request.POST.get('price'),
                description=request.POST.get('description'),
                image=request.FILES.get('image')
            )
            
            # Add sizes if provided
            size_ids = request.POST.getlist('sizes')
            if size_ids:
                product.sizes.set(size_ids)
            
            messages.success(request, f'Product "{product.name}" added successfully!')
            return redirect('dashboard:product_list')
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
    
    sizes = Size.objects.all()
    context = {
        'categories': Product.CATEGORY_CHOICES,
        'sizes': sizes,
        **get_notification_counts(),
    }
    return render(request, 'dashboard/product_form.html', context)


@staff_member_required
def product_edit(request, product_id):
    """Edit existing product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            product.name = request.POST.get('name')
            product.category = request.POST.get('category')
            product.price = request.POST.get('price')
            product.description = request.POST.get('description')
            
            if request.FILES.get('image'):
                product.image = request.FILES.get('image')
            
            product.save()
            
            # Update sizes
            size_ids = request.POST.getlist('sizes')
            product.sizes.set(size_ids)
            
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('dashboard:product_list')
        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')
    
    sizes = Size.objects.all()
    context = {
        'product': product,
        'categories': Product.CATEGORY_CHOICES,
        'sizes': sizes,
        **get_notification_counts(),
    }
    return render(request, 'dashboard/product_form.html', context)


@staff_member_required
def product_delete(request, product_id):
    """Delete product"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('dashboard:product_list')
    
    return render(request, 'dashboard/product_confirm_delete.html', {
        'product': product,
        **get_notification_counts(),
    })


# ==================== DOG MANAGEMENT ====================

@staff_member_required
def dog_list(request):
    """List all dog listings with filter"""
    status = request.GET.get('status', '')
    
    dogs = Dog.objects.all().select_related('lister')
    
    if status == 'pending':
        dogs = dogs.filter(is_approved=False)
    elif status == 'approved':
        dogs = dogs.filter(is_approved=True, is_adopted=False)
    elif status == 'adopted':
        dogs = dogs.filter(is_adopted=True)
    
    dogs = dogs.order_by('-created_at')
    
    context = {
        'dogs': dogs,
        'selected_status': status,
        **get_notification_counts(),
    }
    return render(request, 'dashboard/dog_list.html', context)


@staff_member_required
def dog_approve(request, dog_id):
    """Approve dog listing"""
    dog = get_object_or_404(Dog, id=dog_id)
    
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        send_email = request.POST.get('send_email') == 'on'
        
        dog.is_approved = True
        dog.save()
        
        # Send approval email if checkbox is checked
        if send_email:
            try:
                send_listing_approved(dog, admin_message=message)
                messages.success(request, f'Dog listing "{dog.name}" approved and email sent!')
            except Exception as e:
                messages.warning(request, f'Dog approved but email failed: {str(e)}')
        else:
            messages.success(request, f'Dog listing "{dog.name}" approved!')
        
        return redirect('dashboard:dog_list')
    
    return render(request, 'dashboard/dog_approve.html', {
        'dog': dog,
        **get_notification_counts(),
    })


@staff_member_required
def dog_reject(request, dog_id):
    """Reject dog listing"""
    dog = get_object_or_404(Dog, id=dog_id)
    
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        send_email = request.POST.get('send_email') == 'on'
        
        if not message:
            messages.error(request, 'Please provide a rejection reason.')
            return render(request, 'dashboard/dog_reject.html', {
                'dog': dog,
                **get_notification_counts(),
            })
        
        # Send rejection email before deleting if checkbox is checked
        if send_email:
            subject = f'Your Dog Listing "{dog.name}" - Action Required'
            email_message = f"""
Dear {dog.lister.first_name},

Thank you for submitting your dog listing for "{dog.name}" on Pethood.

Unfortunately, we cannot approve your listing at this time for the following reason:

{message}

If you have any questions or would like to resubmit with corrections, please feel free to contact us or submit a new listing.

Best regards,
The Pethood Team
            """
            
            try:
                send_mail(
                    subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [dog.lister.email],
                    fail_silently=False,
                )
                messages.success(request, f'Dog listing "{dog.name}" rejected and email sent.')
            except Exception as e:
                messages.warning(request, f'Dog rejected but email failed: {str(e)}')
        else:
            messages.success(request, f'Dog listing "{dog.name}" rejected.')
        
        # Delete the dog listing
        dog.delete()
        return redirect('dashboard:dog_list')
    
    return render(request, 'dashboard/dog_reject.html', {
        'dog': dog,
        **get_notification_counts(),
    })


@staff_member_required
def dog_mark_adopted(request, dog_id):
    """Mark approved dog as adopted"""
    dog = get_object_or_404(Dog, id=dog_id)
    
    if request.method == 'POST':
        send_email = request.POST.get('send_email') == 'on'
        
        dog.is_adopted = True
        dog.save()
        
        # Send notification email if checkbox is checked
        if send_email:
            subject = f'Your Dog "{dog.name}" has been Marked as Adopted!'
            email_message = f"""
Dear {dog.lister.first_name},

Congratulations! Your dog listing for "{dog.name}" has been marked as adopted on Pethood.

We're thrilled that {dog.name} has found a loving home!

Best regards,
The Pethood Team
            """
            
            try:
                send_mail(
                    subject,
                    email_message,
                    settings.DEFAULT_FROM_EMAIL,
                    [dog.lister.email],
                    fail_silently=False,
                )
                messages.success(request, f'Dog "{dog.name}" marked as adopted and email sent!')
            except Exception as e:
                messages.warning(request, f'Dog marked as adopted but email failed: {str(e)}')
        else:
            messages.success(request, f'Dog "{dog.name}" marked as adopted!')
        
        return redirect('dashboard:dog_list')
    
    return render(request, 'dashboard/dog_adopt.html', {
        'dog': dog,
        **get_notification_counts(),
    })


# ==================== USER MANAGEMENT ====================

@staff_member_required
def user_list(request):
    """List all users"""
    query = request.GET.get('q', '')
    
    users = User.objects.all().annotate(
        order_count=Count('order'),
        dog_count=Count('listed_dogs')
    )
    
    if query:
        users = users.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    
    users = users.order_by('-date_joined')
    
    context = {
        'users': users,
        'query': query,
        **get_notification_counts(),
    }
    return render(request, 'dashboard/user_list.html', context)


@staff_member_required
def user_detail(request, user_id):
    """View user details with order and dog history"""
    user = get_object_or_404(User, id=user_id)
    
    orders = Order.objects.filter(user=user).order_by('-created_at')
    dogs = Dog.objects.filter(lister=user).order_by('-created_at')
    
    # Statistics
    total_spent = orders.exclude(status='cancelled').aggregate(
        total=Sum('total_amount')
    )['total'] or Decimal('0.00')
    
    context = {
        'viewed_user': user,
        'orders': orders,
        'dogs': dogs,
        'total_spent': total_spent,
        **get_notification_counts(),
    }
    return render(request, 'dashboard/user_detail.html', context)


# ==================== ORDER MANAGEMENT ====================

@staff_member_required
def order_list(request):
    """List all orders with filter"""
    status = request.GET.get('status', '')
    
    orders = Order.objects.all().select_related('user').prefetch_related('items__product')
    
    if status:
        orders = orders.filter(status=status)
    
    orders = orders.order_by('-created_at')
    
    context = {
        'orders': orders,
        'status_choices': Order.STATUS_CHOICES,
        'selected_status': status,
        **get_notification_counts(),
    }
    return render(request, 'dashboard/order_list.html', context)


@staff_member_required
def order_detail(request, order_id):
    """View and manage order details"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        send_email = request.POST.get('send_email') == 'on'
        
        if new_status and new_status in dict(Order.STATUS_CHOICES):
            old_status = order.get_status_display()
            order.status = new_status
            order.save()
            
            # Send status update email if checkbox is checked
            if send_email:
                subject = f'Order #{order.order_number} - Status Update'
                email_message = f"""
Dear {order.first_name},

Your order #{order.order_number} status has been updated:

Previous Status: {old_status}
New Status: {order.get_status_display()}

You can view your order details in your profile on Pethood.

Best regards,
The Pethood Team
                """
                
                try:
                    send_mail(
                        subject,
                        email_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [order.email],
                        fail_silently=False,
                    )
                    messages.success(request, f'Order status updated to "{order.get_status_display()}" and email sent!')
                except Exception as e:
                    messages.warning(request, f'Status updated but email failed: {str(e)}')
            else:
                messages.success(request, f'Order status updated to "{order.get_status_display()}"!')
            
            return redirect('dashboard:order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'status_choices': Order.STATUS_CHOICES,
        **get_notification_counts(),
    }
    return render(request, 'dashboard/order_detail.html', context)
