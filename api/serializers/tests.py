from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from tests.models import Test, Question, Answer, MatchingPair, OrderingItem


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Test',
            value={
                'id': 1,
                'course': 1,
                'title': 'Python Quiz',
                'description': 'Basics',
                'passing_score': 70,
                'evaluation_type': 'AUTO',
                'attempts': 1,
                'warning_threshold': 50,
                'success_threshold': 70,
                'retake_requires_new_attempt': True,
                'due_date': '2026-04-01',
                'is_published': True,
                'created_by': 2,
            },
            response_only=True,
        )
    ]
)
class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = [
            'id',
            'course',
            'title',
            'description',
            'passing_score',
            'evaluation_type',
            'attempts',
            'warning_threshold',
            'success_threshold',
            'retake_requires_new_attempt',
            'due_date',
            'is_published',
            'created_by',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate_passing_score(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('Проходной балл должен быть от 0 до 100.')
        return value

    def validate_attempts(self, value):
        if value < 1:
            raise serializers.ValidationError('Количество попыток должно быть не меньше 1.')
        return value

    def validate_warning_threshold(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('Порог предупреждения должен быть от 0 до 100.')
        return value

    def validate_success_threshold(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError('Порог успеха должен быть от 0 до 100.')
        return value

    def validate(self, attrs):
        attrs = super().validate(attrs)
        warning = attrs.get('warning_threshold', getattr(self.instance, 'warning_threshold', None))
        success = attrs.get('success_threshold', getattr(self.instance, 'success_threshold', None))
        if warning is not None and success is not None and warning >= success:
            raise serializers.ValidationError(
                {'success_threshold': 'Порог успеха должен быть больше порога предупреждения.'}
            )
        return attrs


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Answer',
            value={'id': 1, 'question': 1, 'text': 'Язык программирования', 'is_correct': True},
            response_only=True,
        )
    ]
)
class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'question', 'text', 'is_correct']


class MatchingPairSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingPair
        fields = ['id', 'question', 'left_text', 'right_text', 'order']


class OrderingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderingItem
        fields = ['id', 'question', 'text', 'position']


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'Question',
            value={
                'id': 1,
                'test': 1,
                'type': 'SINGLE',
                'text': 'What is Python?',
                'points': 1,
            },
            response_only=True,
        )
    ]
)
class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    matching_pairs = serializers.SerializerMethodField()
    ordering_items = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            'id',
            'test',
            'type',
            'text',
            'points',
            'image',
            'answers',
            'matching_pairs',
            'ordering_items',
        ]

    def get_matching_pairs(self, obj):
        if not hasattr(obj, 'matching_pairs'):
            return []
        return MatchingPairSerializer(obj.matching_pairs.all(), many=True).data

    def get_ordering_items(self, obj):
        if not hasattr(obj, 'ordering_items'):
            return []
        return OrderingItemSerializer(obj.ordering_items.all(), many=True).data


class MatchSubmissionSerializer(serializers.Serializer):
    left_id = serializers.IntegerField()
    right_id = serializers.IntegerField()


class QuestionSubmissionSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    answer = serializers.IntegerField(required=False)
    answers = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
    )
    matches = MatchSubmissionSerializer(many=True, required=False)
    order = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
    )
    text = serializers.CharField(required=False, allow_blank=True)


class TestSubmissionSerializer(serializers.Serializer):
    answers = QuestionSubmissionSerializer(many=True, required=False)
