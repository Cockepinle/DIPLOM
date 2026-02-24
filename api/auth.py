from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework import generics
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from drf_spectacular.utils import extend_schema, OpenApiExample

from api.serializers import UserSerializer
from users.models import Specialty, Position

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    specialty = serializers.PrimaryKeyRelatedField(queryset=Specialty.objects.filter(is_active=True))
    position = serializers.PrimaryKeyRelatedField(
        queryset=Position.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        email = (value or '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('Email is already registered.')
        return email

    def validate(self, attrs):
        password = attrs.get('password')
        password2 = attrs.get('password2')
        if password != password2:
            raise serializers.ValidationError({'password2': 'Passwords do not match.'})
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)}) from exc
        return attrs

    def create(self, validated_data):
        email = validated_data['email']
        specialty = validated_data['specialty']
        position = validated_data.get('position')
        user = User(
            email=email,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role='EMPLOYEE',
            is_active=True,
            is_staff=False,
            is_superuser=False,
            specialty=specialty,
            position=position,
        )
        user.set_password(validated_data['password'])
        user.save()
        return user


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=['Auth'],
        description='Register a new user. Email is used as login.',
        examples=[
            OpenApiExample(
                'RegisterRequest',
                value={
                    'email': 'user@example.com',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'specialty': 1,
                    'position': 1,
                    'password': 'StrongPass123!',
                    'password2': 'StrongPass123!',
                },
                request_only=True,
            ),
            OpenApiExample(
                'RegisterResponse',
                value={
                'id': 1,
                'email': 'user@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'EMPLOYEE',
            },
                response_only=True,
            ),
        ],
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = UserSerializer(user, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Allow login with email via 'login' field."""

    def get_fields(self):
        fields = super().get_fields()
        fields[self.username_field].required = False
        fields['login'] = serializers.CharField(required=False)
        return fields

    def validate(self, attrs):
        login = attrs.get('login') or attrs.get(self.username_field)
        if not login:
            raise serializers.ValidationError({'login': 'Email is required.'})
        attrs[self.username_field] = login
        return super().validate(attrs)


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    @extend_schema(
        tags=['Auth'],
        description='Obtain JWT access and refresh tokens using email.',
        examples=[
            OpenApiExample(
                'TokenRequest',
                summary='Login',
                value={'login': 'user@example.com', 'password': 'secret'},
                request_only=True,
            ),
            OpenApiExample(
                'TokenResponse',
                summary='Tokens',
                value={'refresh': 'jwt-refresh-token', 'access': 'jwt-access-token'},
                response_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    @extend_schema(
        tags=['Auth'],
        description='Refresh JWT access token.',
        examples=[
            OpenApiExample(
                'RefreshRequest',
                value={'refresh': 'jwt-refresh-token'},
                request_only=True,
            ),
            OpenApiExample(
                'RefreshResponse',
                value={'access': 'jwt-access-token'},
                response_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenVerifyView(TokenVerifyView):
    @extend_schema(
        tags=['Auth'],
        description='Verify JWT access token.',
        examples=[
            OpenApiExample(
                'VerifyRequest',
                value={'token': 'jwt-access-token'},
                request_only=True,
            ),
            OpenApiExample(
                'VerifyResponse',
                value={},
                response_only=True,
            ),
        ],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
