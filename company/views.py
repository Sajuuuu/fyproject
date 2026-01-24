from django.shortcuts import render

# Create your views here.

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def terms_of_use(request):
    return render(request, 'terms_of_use.html')

def about_us(request):
    return render(request, 'about_us.html')
