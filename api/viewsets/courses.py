from django.db import transaction
from django.utils.dateparse import parse_date
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from api.permissions import RolePermission
from api.viewsets.base import BaseModelViewSet
from api.serializers import (
    CourseSerializer,
    CourseMaterialSerializer,
    EnrollmentSerializer,
    TaskSerializer,
    TaskAssignmentSerializer,
    TaskSubmissionSerializer,
)
from courses.models import (
    Course,
    CourseMaterial,
    Enrollment,
    Task,
    TaskAssignment,
    TaskSubmission,
)
from users.models import User

ROLE_EMPLOYEE = 'EMPLOYEE'
ROLE_MANAGER = 'MANAGER'
ROLE_ANALYST = 'ANALYST'
ROLE_ADMIN = 'ADMIN'


class CourseViewSet(BaseModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    schema_tags = ['Courses']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'title', 'created_at']
    filterset_fields = ['specialty', 'is_active', 'created_by']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CourseMaterialViewSet(BaseModelViewSet):
    """Course materials."""
    queryset = CourseMaterial.objects.all()
    serializer_class = CourseMaterialSerializer
    schema_tags = ['Course Materials']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    ordering_fields = ['id', 'order']
    filterset_fields = ['course', 'test', 'material_type', 'is_required']


class EnrollmentViewSet(BaseModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    schema_tags = ['Enrollments']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    ordering_fields = ['id', 'assigned_at', 'due_date', 'progress']
    filterset_fields = ['user', 'course', 'status', 'assigned_by']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]:
            return Enrollment.objects.all()
        return Enrollment.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)

    @action(detail=False, methods=['post'], url_path='assign-all')
    def assign_all(self, request):
        course_id = request.data.get('course')
        if not course_id:
            return Response({'course': 'Course is required.'}, status=400)
        try:
            course = Course.objects.select_related('specialty').get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'course': 'Course not found.'}, status=404)

        if not course.specialty_id:
            return Response(
                {'course': 'Course must have a specialty to assign users.'},
                status=400,
            )

        due_date = request.data.get('due_date')
        if due_date:
            parsed_due_date = parse_date(due_date)
            if not parsed_due_date:
                return Response({'due_date': 'Invalid date format (YYYY-MM-DD).'}, status=400)
            due_date = parsed_due_date

        users = User.objects.filter(
            role=ROLE_EMPLOYEE,
            specialty_id=course.specialty_id,
            is_active=True,
        ).only('id')
        eligible_count = users.count()

        existing_user_ids = set(
            Enrollment.objects.filter(course=course, user__in=users).values_list('user_id', flat=True)
        )

        to_create = []
        for user in users:
            if user.id in existing_user_ids:
                continue
            to_create.append(
                Enrollment(
                    user=user,
                    course=course,
                    assigned_by=request.user,
                    due_date=due_date,
                )
            )

        with transaction.atomic():
            Enrollment.objects.bulk_create(to_create)

        return Response(
            {
                'course': course.id,
                'specialty': course.specialty_id,
                'eligible': eligible_count,
                'created': len(to_create),
                'skipped': len(existing_user_ids),
            }
        )


class TaskViewSet(BaseModelViewSet):
    """Tasks for courses."""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    schema_tags = ['Tasks']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'title', 'created_at', 'due_date']
    filterset_fields = ['course', 'task_type', 'is_active', 'is_published', 'created_by']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TaskAssignmentViewSet(BaseModelViewSet):
    """Task assignments to users."""
    queryset = TaskAssignment.objects.all()
    serializer_class = TaskAssignmentSerializer
    schema_tags = ['Task Assignments']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    ordering_fields = ['id', 'assigned_at', 'due_date', 'priority']
    filterset_fields = ['task', 'user', 'status', 'assigned_by']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]:
            return TaskAssignment.objects.all()
        return TaskAssignment.objects.filter(user=user)

    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


class TaskSubmissionViewSet(BaseModelViewSet):
    """Submissions for assigned tasks."""
    queryset = TaskSubmission.objects.all()
    serializer_class = TaskSubmissionSerializer
    schema_tags = ['Task Submissions']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_EMPLOYEE]
    ordering_fields = ['id', 'submitted_at', 'reviewed_at', 'score']
    filterset_fields = ['assignment', 'status', 'reviewer']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]:
            return TaskSubmission.objects.all()
        return TaskSubmission.objects.filter(assignment__user=user)

    def perform_create(self, serializer):
        user = self.request.user
        assignment = serializer.validated_data.get('assignment')
        if user.role == ROLE_EMPLOYEE and assignment.user_id != user.id:
            raise PermissionDenied('You can only submit your own assignments.')
        serializer.save()
