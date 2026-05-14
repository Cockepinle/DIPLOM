from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from feedback.models import Feedback, TaskReview


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Feedback',
            value={
                'id': 1,
                'manager': 2,
                'test_result': 1,
                'comment': 'Отличная работа',
                'rating': 5,
                'created_at': '2026-02-05T10:00:00Z',
            },
            response_only=True,
        )
    ]
)
class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = ['id', 'manager', 'test_result', 'comment', 'rating', 'created_at']
        read_only_fields = ['manager', 'created_at']

    def validate_rating(self, value):
        if value is None:
            return value
        if value < 1 or value > 5:
            raise serializers.ValidationError('Оценка должна быть от 1 до 5.')
        return value


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'TaskReview',
            value={
                'id': 1,
                'manager': 2,
                'task_submission': 1,
                'comment': 'Нужно доработать',
                'rating': 4,
                'created_at': '2026-02-05T10:00:00Z',
            },
            response_only=True,
        )
    ]
)
class TaskReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskReview
        fields = ['id', 'manager', 'task_submission', 'comment', 'rating', 'created_at']
        read_only_fields = ['manager', 'created_at']

    def validate_rating(self, value):
        if value is None:
            return value
        if value < 1 or value > 5:
            raise serializers.ValidationError('Оценка должна быть от 1 до 5.')
        return value
