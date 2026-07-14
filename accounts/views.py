"""
Views for accounts app - Authentication and User Management
"""

import uuid
from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.exceptions import TokenError
from .models import User
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UpdateProfileSerializer, ChangePasswordSerializer,
    ForgotPasswordSerializer, ResetPasswordSerializer, AdminUserSerializer
)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'success': True,
                'message': 'Registration successful.',
                'user': UserSerializer(user, context={'request': request}).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_201_CREATED)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            return Response({
                'success': True,
                'message': 'Login successful.',
                'user': UserSerializer(user, context={'request': request}).data,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({
                'success': True,
                'message': 'Logged out successfully.'
            }, status=status.HTTP_200_OK)
        except TokenError:
            return Response({
                'success': False,
                'message': 'Invalid token.'
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user, context={'request': request})
        return Response({'success': True, 'user': serializer.data})

    def put(self, request):
        serializer = UpdateProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'success': True,
                'message': 'Profile updated successfully.',
                'user': UserSerializer(user, context={'request': request}).data
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({
                'success': True,
                'message': 'Password changed successfully.'
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            token = str(uuid.uuid4())
            user.reset_password_token = token
            user.reset_password_expires = timezone.now() + timedelta(hours=1)
            user.save(update_fields=['reset_password_token', 'reset_password_expires'])

            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

            try:
                html_message = render_to_string('emails/password_reset.html', {
                    'user': user,
                    'reset_url': reset_url,
                    'app_name': settings.APP_NAME,
                })
                send_mail(
                    subject=f'Password Reset - {settings.APP_NAME}',
                    message=f'Click this link to reset your password: {reset_url}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                pass  # Log error but still return success for security

            return Response({
                'success': True,
                'message': 'Password reset email sent. Please check your inbox.'
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            token = serializer.validated_data['token']
            try:
                user = User.objects.get(
                    reset_password_token=token,
                    reset_password_expires__gt=timezone.now()
                )
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'Invalid or expired reset token.'
                }, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data['new_password'])
            user.reset_password_token = None
            user.reset_password_expires = None
            user.save()

            return Response({
                'success': True,
                'message': 'Password reset successfully. You can now login.'
            })
        return Response({
            'success': False,
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# Admin Views
class AdminUsersView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)

        users = User.objects.all().order_by('-date_joined')
        search = request.query_params.get('search', '')
        if search:
            users = users.filter(
                email__icontains=search
            ) | users.filter(
                first_name__icontains=search
            ) | users.filter(
                last_name__icontains=search
            )

        serializer = AdminUserSerializer(users, many=True)
        return Response({
            'success': True,
            'count': users.count(),
            'users': serializer.data
        })


class AdminUserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(pk=pk)
            if user == request.user:
                return Response({
                    'success': False,
                    'message': 'You cannot delete your own account.'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.delete()
            return Response({'success': True, 'message': 'User deleted successfully.'})
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        if not request.user.is_admin:
            return Response({'detail': 'Access denied.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            user = User.objects.get(pk=pk)
            is_active = request.data.get('is_active')
            if is_active is not None:
                user.is_active = is_active
                user.save(update_fields=['is_active'])
            return Response({
                'success': True,
                'message': f"User {'activated' if is_active else 'deactivated'} successfully.",
                'user': AdminUserSerializer(user).data
            })
        except User.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)
