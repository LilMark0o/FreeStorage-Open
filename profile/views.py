import random
import string
from django.shortcuts import get_object_or_404, redirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .forms import ProfileUpdateForm  # You'll need to create this form
from django.shortcuts import render

# Create your views here.
# views.py
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.models import User
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from authentication.models import UserProfile
from django.contrib.auth import logout

# View to update user profile


@login_required
def profile_view(request):
    user = request.user
    if user.first_name == '':
        user.first_name = '[Not defined yet]'
    if user.last_name == '':
        user.last_name = '[Not defined yet]'
    return render(request, 'profile/profile.html', {'user': user})

# Delete user account


@login_required
def delete_account(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        user.delete()
        logout(request)
        messages.success(
            request, 'Your account has been deleted successfully.')
        return redirect('home')  # Redirect to homepage after deletion

    # Redirect back to profile if method is not POST
    return redirect('profile')


def verify_email(request, code):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)
    token = code

    if user and user_profile.verification_code == token:
        user_profile.authenticated = True  # Activate the user
        user_profile.save()
        messages.success(request, "Your email has been verified successfully.")
        return redirect('login')  # or any other page
    else:
        messages.error(request, "The verification link is invalid.")
        return redirect('home')


@login_required
def update_profile(request, pk):
    user = get_object_or_404(User, pk=pk)

    # Ensure the user can only update their own profile
    if user != request.user:
        messages.error(request, "You cannot update another user's profile.")
        return redirect('profile')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')

        # Now you can update the user instance
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        if user.email != email:
            user.email = email
            profile = UserProfile.objects.get(user=user)
            profile.authenticated = False
            profile.save()
            user.save()
            send_verification_email(user)
            messages.success(
                request, 'Please verify your email address by clicking the link sent to your email.')
            return redirect('profile')
        user.save()

        messages.success(request, 'Your profile was successfully updated!')
        return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=user)

    return render(request, 'profile/update_profile.html', {'form': form})


def generateCode():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))


def send_verification_email(user):
    subject = 'Verify your email address'
    code = generateCode()
    profile = UserProfile.objects.get(user=user)
    profile.verification_code = code
    profile.save()
    verify_link = f"{settings.SITE_URL}/app/profile/verify/{code}/"

    # Format the message in plain text
    message = f"Hi {
        user.username}, please verify your email address by clicking the link below:\n{verify_link}"

    email_from = settings.EMAIL_HOST_USER
    recipient_list = [user.email]

    try:
        send_mail(subject, message, email_from, recipient_list)
    except Exception as e:
        try:
            send_mail(subject, message, email_from, recipient_list)
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    return True


@login_required
def authenticate(request, pk):
    user = get_object_or_404(User, pk=pk)

    # Ensure the user can only update their own profile
    if user != request.user:
        messages.error(
            request, "You cannot authenticate another user's profile.")
        return redirect('profile')

    send_verification_email(user)

    messages.success(request, 'Email verification link has been sent.')

    return redirect('profile')
