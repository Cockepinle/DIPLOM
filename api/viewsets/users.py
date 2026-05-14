from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from api.permissions import RolePermission, IsAdminOrSelf
from api.viewsets.base import BaseModelViewSet
from api.serializers import (
    UserSerializer,
    SpecialtySerializer,
    PositionSerializer,
    CompetencySerializer,
    UserCompetencySerializer,
    CompetencyAssessmentSerializer,
)
from users.models import Specialty, Position, Competency, UserCompetency, CompetencyAssessment

User = get_user_model()

ROLE_EMPLOYEE = 'EMPLOYEE'
ROLE_MANAGER = 'MANAGER'
ROLE_ANALYST = 'ANALYST'
ROLE_ADMIN = 'ADMIN'


class UserViewSet(BaseModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    schema_tags = ['Users']
    search_fields = ['email', 'first_name', 'last_name', 'position__name']
    ordering_fields = ['id', 'last_name', 'date_joined']
    filterset_fields = ['role', 'department', 'position', 'specialty', 'is_active', 'registration_status']

    def get_permissions(self):
        if self.action == 'list':
            self.read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]
            self.write_roles = [ROLE_ADMIN]
        elif self.action == 'retrieve':
            self.read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
            self.write_roles = [ROLE_ADMIN]
        elif self.action in ['update', 'partial_update']:
            self.read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
            self.write_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
            return [IsAuthenticated(), RolePermission(), IsAdminOrSelf()]
        elif self.action in ['approve_registration', 'reject_registration']:
            self.read_roles = [ROLE_ADMIN]
            self.write_roles = [ROLE_ADMIN]
        elif self.action in ['create', 'destroy']:
            self.read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]
            self.write_roles = [ROLE_ADMIN]
        else:
            self.read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
            self.write_roles = [ROLE_ADMIN]
        return [IsAuthenticated(), RolePermission()]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
        if getattr(user, 'is_superuser', False) or user.role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]:
            return User.objects.all()
        return User.objects.filter(pk=user.pk)

    @action(detail=True, methods=['post'], url_path='registration/approve')
    def approve_registration(self, request, pk=None):
        user = request.user
        if not (getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == ROLE_ADMIN):
            return Response({'detail': 'Недостаточно прав.'}, status=status.HTTP_403_FORBIDDEN)
        target = self.get_object()
        comment = (request.data.get('comment') or '').strip()
        now = timezone.now()
        target.is_active = True
        target.registration_status = User.RegistrationStatus.APPROVED
        target.registration_reviewed_at = now
        target.registration_reviewed_by = user
        target.registration_review_comment = comment
        target.save(
            update_fields=[
                'is_active',
                'registration_status',
                'registration_reviewed_at',
                'registration_reviewed_by',
                'registration_review_comment',
            ]
        )
        return Response(self.get_serializer(target).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='registration/reject')
    def reject_registration(self, request, pk=None):
        user = request.user
        if not (getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == ROLE_ADMIN):
            return Response({'detail': 'Недостаточно прав.'}, status=status.HTTP_403_FORBIDDEN)
        target = self.get_object()
        comment = (request.data.get('comment') or '').strip()
        now = timezone.now()
        target.is_active = False
        target.registration_status = User.RegistrationStatus.REJECTED
        target.registration_reviewed_at = now
        target.registration_reviewed_by = user
        target.registration_review_comment = comment
        target.save(
            update_fields=[
                'is_active',
                'registration_status',
                'registration_reviewed_at',
                'registration_reviewed_by',
                'registration_review_comment',
            ]
        )
        return Response(self.get_serializer(target).data, status=status.HTTP_200_OK)


class SpecialtyViewSet(BaseModelViewSet):
    """Specialty catalog."""
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer
    schema_tags = ['Specialties']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name', 'created_at']
    filterset_fields = ['is_active']


class PositionViewSet(BaseModelViewSet):
    """Position catalog."""
    queryset = Position.objects.all()
    serializer_class = PositionSerializer
    schema_tags = ['Positions']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['name', 'description']
    ordering_fields = ['id', 'name', 'created_at']
    filterset_fields = ['is_active']


class CompetencyViewSet(BaseModelViewSet):
    """Competency catalog."""
    queryset = Competency.objects.all()
    serializer_class = CompetencySerializer
    schema_tags = ['Competencies']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['name', 'description', 'category']
    ordering_fields = ['id', 'name', 'created_at']
    filterset_fields = ['is_active', 'category']


class UserCompetencyViewSet(BaseModelViewSet):
    """User competency levels."""
    queryset = UserCompetency.objects.all()
    serializer_class = UserCompetencySerializer
    schema_tags = ['User Competencies']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    ordering_fields = ['id', 'level', 'updated_at']
    filterset_fields = ['user', 'competency', 'source']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]:
            return UserCompetency.objects.all()
        return UserCompetency.objects.filter(user=user)


class CompetencyAssessmentViewSet(BaseModelViewSet):
    """Competency assessments."""
    queryset = CompetencyAssessment.objects.all()
    serializer_class = CompetencyAssessmentSerializer
    schema_tags = ['Competency Assessments']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    ordering_fields = ['id', 'assessed_at', 'level']
    filterset_fields = ['user', 'assessor', 'competency']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]:
            return CompetencyAssessment.objects.all()
        return CompetencyAssessment.objects.filter(user=user)
