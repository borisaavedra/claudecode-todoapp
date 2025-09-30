from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
import secrets
from .forms import SignUpForm, LoginForm, ProfileUpdateForm, ProfileDetailUpdateForm, PasswordResetRequestForm
from .models import Profile


def home(request):
    return render(request, 'home.html', {})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Usuario inactivo hasta verificar email
            user.save()

            # Generar token de verificación
            profile = user.profile
            profile.verification_token = secrets.token_urlsafe(32)
            profile.save()

            # Enviar email de verificación
            verification_url = request.build_absolute_uri(
                reverse('verify_email', kwargs={'token': profile.verification_token})
            )
            subject = 'Verifica tu cuenta'
            message = f'Hola {user.username},\n\nPor favor verifica tu cuenta haciendo clic en el siguiente enlace:\n{verification_url}'

            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

            messages.success(request, 'Cuenta creada exitosamente. Por favor verifica tu email para activar tu cuenta.')
            return redirect('login')
    else:
        form = SignUpForm()

    return render(request, 'registration/signup.html', {'form': form})


def verify_email(request, token):
    try:
        profile = Profile.objects.get(verification_token=token)
        user = profile.user
        user.is_active = True
        user.save()
        profile.email_verified = True
        profile.verification_token = None
        profile.save()
        messages.success(request, 'Email verificado exitosamente. Ahora puedes iniciar sesión.')
        return redirect('login')
    except Profile.DoesNotExist:
        messages.error(request, 'Token de verificación inválido.')
        return redirect('home')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    messages.success(request, f'Bienvenido {user.username}!')
                    next_url = request.GET.get('next', 'home')
                    return redirect(next_url)
                else:
                    messages.error(request, 'Tu cuenta no está activa. Por favor verifica tu email.')
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')
    else:
        form = LoginForm()

    return render(request, 'registration/login.html', {'form': form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente.')
    return redirect('home')


@login_required
def profile_view(request):
    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileDetailUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Tu perfil ha sido actualizado exitosamente.')
            return redirect('profile')
    else:
        user_form = ProfileUpdateForm(instance=request.user)
        profile_form = ProfileDetailUpdateForm(instance=request.user.profile)

    context = {
        'user_form': user_form,
        'profile_form': profile_form
    }
    return render(request, 'registration/profile.html', context)


def password_reset_request(request):
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))

                reset_url = request.build_absolute_uri(
                    reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})
                )

                subject = 'Recuperación de contraseña'
                message = f'Hola {user.username},\n\nHaz clic en el siguiente enlace para restablecer tu contraseña:\n{reset_url}'

                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])
                messages.success(request, 'Se ha enviado un email con instrucciones para restablecer tu contraseña.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'No existe una cuenta con ese email.')
    else:
        form = PasswordResetRequestForm()

    return render(request, 'registration/password_reset.html', {'form': form})


def password_reset_confirm(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == 'POST':
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')

            if password1 and password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, 'Tu contraseña ha sido actualizada exitosamente.')
                return redirect('login')
            else:
                messages.error(request, 'Las contraseñas no coinciden.')

        return render(request, 'registration/password_reset_confirm.html', {'validlink': True})
    else:
        messages.error(request, 'El enlace de recuperación es inválido o ha expirado.')
        return redirect('password_reset_request')