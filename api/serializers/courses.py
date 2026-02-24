from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from courses.models import (
    Course,
    CourseMaterial,
    Enrollment,
    Task,
    TaskAssignment,
    TaskSubmission,
)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Course',
            value={
                'id': 1,
                'title': 'Python Basics',
                'description': 'Intro course',
                'specialty': 1,
                'created_by': 2,
                'is_active': True,
            },
            response_only=True,
        )
    ]
)
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'specialty',
            'created_by',
            'created_at',
            'updated_at',
            'is_active',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        request = self.context.get('request')
        if request and request.user and getattr(request.user, 'role', None) == 'MANAGER':
            specialty = attrs.get('specialty', getattr(self.instance, 'specialty', None))
            if not specialty:
                raise serializers.ValidationError(
                    {'specialty': 'Специальность обязательна при создании курса менеджером.'}
                )
        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'CourseMaterial',
            value={
                'id': 1,
                'course': 1,
                'title': 'Lecture 1',
                'material_type': 'TEXT',
                'content': 'Intro content',
                'order': 1,
                'is_required': True,
            },
            response_only=True,
        )
    ]
)
class CourseMaterialSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseMaterial
        fields = [
            'id',
            'course',
            'test',
            'title',
            'material_type',
            'content',
            'url',
            'file',
            'image',
            'accent_color',
            'order',
            'is_required',
        ]

    def validate(self, attrs):
        course = attrs.get('course') or getattr(self.instance, 'course', None)
        test = attrs.get('test', getattr(self.instance, 'test', None))
        if test and course and test.course_id != course.id:
            raise serializers.ValidationError({'test': 'Тест не относится к выбранному курсу.'})
        material_type = attrs.get('material_type') or getattr(self.instance, 'material_type', None)
        content = attrs.get('content', getattr(self.instance, 'content', None))
        url = attrs.get('url', getattr(self.instance, 'url', None))
        file = attrs.get('file', getattr(self.instance, 'file', None))
        if material_type == CourseMaterial.MaterialType.TEXT and not content:
            raise serializers.ValidationError({'content': 'Content is required for TEXT materials.'})
        if material_type == CourseMaterial.MaterialType.LINK and not url:
            raise serializers.ValidationError({'url': 'URL is required for LINK materials.'})
        if material_type == CourseMaterial.MaterialType.FILE and not file:
            raise serializers.ValidationError({'file': 'File is required for FILE materials.'})
        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Enrollment',
            value={
                'id': 1,
                'user': 1,
                'course': 2,
                'assigned_by': 3,
                'due_date': '2026-05-01',
                'status': 'ASSIGNED',
                'progress': '0.00',
                'completed': False,
            },
            response_only=True,
        )
    ]
)
class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = [
            'id',
            'user',
            'course',
            'assigned_by',
            'assigned_at',
            'due_date',
            'started_at',
            'completed_at',
            'status',
            'progress',
            'completed',
        ]
        read_only_fields = ['assigned_by', 'assigned_at']

    def validate(self, attrs):
        user = attrs.get('user', getattr(self.instance, 'user', None))
        course = attrs.get('course', getattr(self.instance, 'course', None))
        if user and course and course.specialty_id and user.specialty_id != course.specialty_id:
            raise serializers.ValidationError(
                {'user': 'Пользователь должен иметь ту же специальность, что и курс.'}
            )
        return attrs

    def validate_progress(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('Progress must be between 0 and 100.')
        return value


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Task',
            value={
                'id': 1,
                'course': 1,
                'title': 'Case study',
                'description': 'Solve the case',
                'attachment': None,
                'task_type': 'CASE',
                'max_score': 100,
                'created_by': 2,
                'is_active': True,
                'is_published': False,
            },
            response_only=True,
        )
    ]
)
class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = [
            'id',
            'course',
            'title',
            'description',
            'attachment',
            'criteria',
            'task_type',
            'max_score',
            'created_by',
            'created_at',
            'updated_at',
            'due_date',
            'is_active',
            'is_published',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate(self, attrs):
        course = attrs.get('course', getattr(self.instance, 'course', None))
        if not course:
            raise serializers.ValidationError({'course': 'Course is required.'})
        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'TaskAssignment',
            value={
                'id': 1,
                'task': 1,
                'user': 1,
                'assigned_by': 2,
                'due_date': '2026-04-15',
                'status': 'ASSIGNED',
                'priority': 3,
            },
            response_only=True,
        )
    ]
)
class TaskAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskAssignment
        fields = [
            'id',
            'task',
            'user',
            'assigned_by',
            'assigned_at',
            'due_date',
            'status',
            'priority',
        ]
        read_only_fields = ['assigned_by', 'assigned_at']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'TaskSubmission',
            value={
                'id': 1,
                'assignment': 1,
                'content': 'My solution',
                'status': 'SUBMITTED',
                'score': 90,
            },
            response_only=True,
        )
    ]
)
class TaskSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskSubmission
        fields = [
            'id',
            'assignment',
            'content',
            'file',
            'submitted_at',
            'status',
            'score',
            'reviewed_at',
            'reviewer',
        ]
        read_only_fields = ['submitted_at', 'reviewed_at', 'reviewer']

    def validate_score(self, value):
        if value is None:
            return value
        if value < 0 or value > 100:
            raise serializers.ValidationError('Score must be between 0 and 100.')
        return value
