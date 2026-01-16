from django.shortcuts import render,redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

# Create your views here.
def home(request):
    return render(request,'home.html')

def signinpage(request):
    error_message = None
   
    if request.method == 'POST':
        uname = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')

        if pass1 != pass2:
            error_message = "Your password and confirm password are not the same!"
        elif User.objects.filter(username__iexact=uname).exists():
            error_message = "Username already exists!"
        elif User.objects.filter(email__iexact=email).exists():
            error_message = "Email already exists!"
        else:
            myuser = User.objects.create_user(username=uname, email=email, password=pass1)
            myuser.save()
            messages.success(request, "Account created successfully! You can now log in.")
            return redirect('login')

    return render(request, 'signup.html', {'error_message': error_message})

def loginpage(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("home")  # Redirect after successful login
        else:
            messages.error(request, "Invalid username or password.")
            return redirect("login")

    return render(request, "login.html")

def logout_view(request):
    logout(request)  # clears session
    return redirect('home')  # redirect wherever you want