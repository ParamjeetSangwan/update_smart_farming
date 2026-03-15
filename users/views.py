# users/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import UserProfile, OTPVerification, Notification, AdminTwoFactor


def create_profile_if_missing(user):
    if not hasattr(user, 'profile'):
        UserProfile.objects.create(user=user, name=user.username)


def send_otp_email(user, purpose):
    """Generate and send OTP email"""
    # Invalidate old OTPs
    OTPVerification.objects.filter(user=user, purpose=purpose, is_used=False).update(is_used=True)

    otp = OTPVerification.generate_otp()
    OTPVerification.objects.create(user=user, otp=otp, purpose=purpose)

    subject_map = {
        'register': '🌾 SmartFarming - Verify Your Email',
        '2fa': '🔐 SmartFarming - Admin Login OTP',
    }

    message = f"""
Hello {user.username},

Your verification code is: {otp}

This code expires in 10 minutes.

If you did not request this, please ignore this email.

— SmartFarming Team 🌾
    """

    send_mail(
        subject_map.get(purpose, 'SmartFarming OTP'),
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
    return otp


# ══════════════════════════════════════════
# FEATURE 1: EMAIL OTP VERIFICATION
# ══════════════════════════════════════════
def register_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return redirect('register')
        if not email or '@' not in email:
            messages.error(request, 'Enter a valid email.')
            return redirect('register')
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return redirect('register')
        if confirm_password and password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return redirect('register')
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
            return redirect('register')

        # Create inactive user — needs OTP verification
        user = User.objects.create_user(
            username=username, email=email, password=password,
            is_active=False  # ← Not active until OTP verified
        )
        UserProfile.objects.create(user=user, name=username)

        # Send OTP
        try:
            send_otp_email(user, 'register')
            request.session['otp_user_id'] = user.id
            messages.success(request, f'OTP sent to {email}. Please verify your email.')
            return redirect('verify_otp')
        except Exception as e:
            # If email fails, activate anyway (dev mode)
            user.is_active = True
            user.save()
            messages.success(request, 'Registration successful! Please log in.')
            return redirect('login')

    return render(request, 'users/register.html')


def verify_otp_view(request):
    """Verify OTP after registration"""
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('register')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('register')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        otp_obj = OTPVerification.objects.filter(
            user=user, purpose='register', is_used=False
        ).last()

        if otp_obj and otp_obj.is_valid() and otp_obj.otp == entered_otp:
            otp_obj.is_used = True
            otp_obj.save()
            user.is_active = True
            user.save()
            del request.session['otp_user_id']
            messages.success(request, '✅ Email verified! You can now log in.')
            return redirect('login')
        else:
            messages.error(request, '❌ Invalid or expired OTP. Try again.')

    return render(request, 'users/verify_otp.html', {'email': user.email})


def resend_otp_view(request):
    """Resend OTP"""
    user_id = request.session.get('otp_user_id')
    if not user_id:
        return redirect('register')
    try:
        user = User.objects.get(id=user_id)
        send_otp_email(user, 'register')
        messages.success(request, 'New OTP sent to your email!')
    except Exception:
        messages.error(request, 'Failed to send OTP. Try again.')
    return redirect('verify_otp')


# ══════════════════════════════════════════
# FEATURE 2: LOGIN WITH 2FA FOR ADMIN
# ══════════════════════════════════════════
def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect('admin_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Check if user is blocked
            if hasattr(user, 'profile') and user.profile.is_blocked:
                messages.error(request, '🚫 Your account has been blocked. Contact support.')
                return render(request, 'users/login.html')

            # If admin — check 2FA
            if user.is_staff:
                two_factor, _ = AdminTwoFactor.objects.get_or_create(user=user)
                if two_factor.is_enabled:
                    # Send 2FA OTP
                    try:
                        send_otp_email(user, '2fa')
                        request.session['2fa_user_id'] = user.id
                        messages.info(request, f'OTP sent to {user.email}')
                        return redirect('verify_2fa')
                    except Exception:
                        pass  # Fall through to normal login if email fails

            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'users/login.html')


def verify_2fa_view(request):
    """Verify 2FA OTP for admin"""
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return redirect('login')

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        otp_obj = OTPVerification.objects.filter(
            user=user, purpose='2fa', is_used=False
        ).last()

        if otp_obj and otp_obj.is_valid() and otp_obj.otp == entered_otp:
            otp_obj.is_used = True
            otp_obj.save()
            del request.session['2fa_user_id']
            login(request, user)
            return redirect('admin_dashboard')
        else:
            messages.error(request, '❌ Invalid or expired OTP.')

    return render(request, 'users/verify_2fa.html', {'email': user.email})


def logout_view(request):
    logout(request)
    return redirect('login')


# ══════════════════════════════════════════
# FEATURE 3: AVATAR UPLOAD IN PROFILE
# ══════════════════════════════════════════
@login_required
def dashboard_view(request):
    create_profile_if_missing(request.user)
    name = request.user.profile.name
    # Get unread notifications count
    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
    notifications = Notification.objects.filter(user=request.user)[:5]
    return render(request, 'dashboard.html', {
        'name': name,
        'unread_count': unread_count,
        'notifications': notifications,
    })


@login_required
def profile_view(request):
    create_profile_if_missing(request.user)
    profile = request.user.profile

    if request.method == 'POST':
        profile.name = request.POST.get('name', profile.name)
        profile.location = request.POST.get('location', '')

        # ── Avatar Upload ──
        if request.FILES.get('avatar'):
            # Delete old avatar if exists
            if profile.avatar:
                import os
                if os.path.isfile(profile.avatar.path):
                    os.remove(profile.avatar.path)
            profile.avatar = request.FILES['avatar']

        profile.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('profile')

    return render(request, 'users/profile.html', {
        'user': request.user,
        'profile': profile,
        'name': profile.name,
        'location': profile.location or ''
    })


# ══════════════════════════════════════════
# FEATURE 4: NOTIFICATIONS
# ══════════════════════════════════════════
@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(user=request.user)
    # Mark all as read when page opened
    notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'users/notifications.html', {
        'notifications': notifications,
        'total': notifications.count(),
    })


@login_required
def mark_notification_read(request, notif_id):
    try:
        notif = Notification.objects.get(id=notif_id, user=request.user)
        notif.is_read = True
        notif.save()
    except Notification.DoesNotExist:
        pass
    return redirect('notifications')


@login_required
def orders_view(request):
    return render(request, 'orders.html')


@login_required
def ai_recommendations_view(request):
    return render(request, 'ai_recommendations.html')


@login_required
def activate_account(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, "Your account has been activated.")
        return redirect('login')
    else:
        messages.error(request, "Activation link is invalid.")
        return redirect('login')