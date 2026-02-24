from django.contrib.auth import get_user_model
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from users.models import Specialty, Position, Competency, UserCompetency, CompetencyAssessment

User = get_user_model()


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'User',
            value={
                'id': 1,
                'email': 'jdoe@example.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'role': 'EMPLOYEE',
                'department': 'Sales',
                'position': 1,
                'specialty': 1,
                'is_active': True,
            },
            response_only=True,
        )
    ]
)
class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    specialty_name = serializers.CharField(source='specialty.name', read_only=True)
    position_name = serializers.CharField(source='position.name', read_only=True)
    password = serializers.CharField(write_only=True, required=False, min_length=8)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'role',
            'role_display',
            'department',
            'position',
            'position_name',
            'specialty',
            'specialty_name',
            'avatar',
            'is_active',
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
            'password',
        ]
        read_only_fields = [
            'is_staff',
            'is_superuser',
            'date_joined',
            'last_login',
        ]

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user and not (
            getattr(request.user, 'is_superuser', False) or getattr(request.user, 'role', None) == 'ADMIN'
        ):
            for field in ['is_staff', 'is_superuser', 'role', 'is_active']:
                attrs.pop(field, None)
        role = attrs.get('role') or (self.instance.role if self.instance else User.Role.EMPLOYEE)
        if role == User.Role.EMPLOYEE:
            specialty = (
                attrs.get('specialty')
                if 'specialty' in attrs
                else (self.instance.specialty if self.instance else None)
            )
            if not specialty:
                raise serializers.ValidationError(
                    {'specialty': 'Специальность обязательна для обычного пользователя.'}
                )
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Specialty',
            value={
                'id': 1,
                'name': 'Data Science',
                'description': 'Analytics and ML',
                'is_active': True,
            },
            response_only=True,
        )
    ]
)
class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['created_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Position',
            value={
                'id': 1,
                'name': 'Программист',
                'description': 'Разработка и поддержка',
                'is_active': True,
            },
            response_only=True,
        )
    ]
)
class PositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Position
        fields = ['id', 'name', 'description', 'is_active', 'created_at']
        read_only_fields = ['created_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Competency',
            value={
                'id': 1,
                'name': 'SQL',
                'description': 'Query databases',
                'category': 'Data',
                'is_active': True,
            },
            response_only=True,
        )
    ]
)
class CompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Competency
        fields = ['id', 'name', 'description', 'category', 'is_active', 'created_at']
        read_only_fields = ['created_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'UserCompetency',
            value={
                'id': 1,
                'user': 1,
                'competency': 1,
                'level': 7,
                'source': 'MANAGER',
            },
            response_only=True,
        )
    ]
)
class UserCompetencySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserCompetency
        fields = ['id', 'user', 'competency', 'level', 'source', 'updated_at']
        read_only_fields = ['updated_at']

    def validate_level(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError('Level must be between 0 and 10.')
        return value


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'CompetencyAssessment',
            value={
                'id': 1,
                'user': 1,
                'assessor': 2,
                'competency': 1,
                'level': 6,
                'comment': 'Good progress',
                'test_result': 1,
                'task_submission': None,
            },
            response_only=True,
        )
    ]
)
class CompetencyAssessmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompetencyAssessment
        fields = [
            'id',
            'user',
            'assessor',
            'competency',
            'level',
            'comment',
            'test_result',
            'task_submission',
            'assessed_at',
        ]
        read_only_fields = ['assessed_at']

    def validate_level(self, value):
        if value < 0 or value > 10:
            raise serializers.ValidationError('Level must be between 0 and 10.')
        return value
