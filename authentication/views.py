import datetime
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import authenticate, login

from .forms import CustomUserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from upload.models import File
from files.views import readableSize
from .models import UserProfile
from django.core.mail import send_mail
from free_storage.settings import BASE_DIR
# Create your views here.


class CustomLoginView(LoginView):
    template_name = 'authentication/login.html'  # Your login template


def custom_404(request, exception):
    return render(request, '404.html', status=404)


def landing(request):
    totalusers = UserProfile.objects.all().count()
    totalfiles = File.objects.all().count()
    totalSizeFiles = readableSize(
        sum(file.size for file in File.objects.all()))
    return render(request, 'authentication/landing.html', {'totalusers': totalusers, 'totalfiles': totalfiles, 'totalSizeFiles': totalSizeFiles})


def home(request):
    if not request.user.is_authenticated:
        return redirect('landing')

    files = File.objects.filter(user=request.user)
    total_file_size = sum(file.size for file in files)
    if len(files) != 0:
        mostRecentFile = files.order_by('-date').first().date
        dateNow = datetime.datetime.now().date()
        dateDifference = dateNow - mostRecentFile
        if (str(dateDifference).split(',')[0]) == '0:00:00':
            dateDifference = 'Today'
        else:
            dateDifference = (str(dateDifference).split(',')[0]) + ' ago'
    else:
        dateDifference = 'Never'
    try:
        profile = request.user.userprofile  # Access the UserProfile
        restSize = profile.storageSize - total_file_size
    except UserProfile.DoesNotExist:
        restSize = 0  # Handle the case where the UserProfile doesn't exist

    used = readableSize(total_file_size)
    restSize = readableSize(restSize)

    return render(request, 'authentication/home.html', {'storageUsed': used, 'restSize': restSize, 'numFiles': len(files),
                                                        'lastUpdate': dateDifference})


def custom_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')  # Redirect to the desired page after login
        else:
            # Debugging: Print form errors to the console
            print("Form errors:", form.errors)
    else:
        form = AuthenticationForm()
        if request.user.is_authenticated:
            return redirect('home')

    return render(request, 'authentication/login.html', {'form': form})


def register(request):
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
        else:
            # Debugging: Print form errors to the console
            print("Form errors:", form.errors)
    else:
        form = CustomUserCreationForm()

    return render(request, 'authentication/register.html', {'form': form})
