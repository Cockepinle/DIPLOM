from rest_framework import serializers
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from results.models import TestResult


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            'TestResult',
            value={
                'id': 1,
                'user': 1,
                'test': 1,
                'score': 80,
                'passed': True,
                'status': 'PASSED',
                'attempt_number': 1,
                'completed_at': '2026-02-05T10:00:00Z',
            },
            response_only=True,
        )
    ]
)
class TestResultSerializer(serializers.ModelSerializer):
    score_color = serializers.SerializerMethodField()

    class Meta:
        model = TestResult
        fields = [
            'id',
            'user',
            'test',
            'score',
            'score_color',
            'passed',
            'status',
            'attempt_number',
            'completed_at',
        ]
        read_only_fields = ['completed_at']

    def validate(self, attrs):
        status = attrs.get('status', getattr(self.instance, 'status', None))
        score = attrs.get('score', getattr(self.instance, 'score', None))
        passed = attrs.get('passed', getattr(self.instance, 'passed', None))

        if status is None:
            if passed is True:
                status = TestResult.Status.PASSED
                attrs['status'] = status
            elif passed is False:
                status = TestResult.Status.FAILED
                attrs['status'] = status
            elif score is not None:
                raise serializers.ValidationError(
                    {'status': 'Статус обязателен, если указан балл.'}
                )

        if status in [TestResult.Status.UNDER_REVIEW, TestResult.Status.RETURNED, TestResult.Status.DECLINED]:
            attrs['score'] = None
            attrs['passed'] = None
            return attrs

        if status in [TestResult.Status.PASSED, TestResult.Status.FAILED]:
            if score is None:
                raise serializers.ValidationError({'score': 'Для проверенного результата нужно указать балл.'})
            expected_passed = status == TestResult.Status.PASSED
            if passed is None:
                attrs['passed'] = expected_passed
            elif passed != expected_passed:
                raise serializers.ValidationError({'passed': 'Поле \"Сдан\" должно соответствовать статусу.'})
        return attrs

    def validate_score(self, value):
        if value is None:
            return value
        if value < 0:
            raise serializers.ValidationError('Балл должен быть не меньше 0.')
        if value > 100:
            raise serializers.ValidationError('Балл не может быть больше 100.')
        return value

    def get_score_color(self, obj):
        if obj.score is None:
            return None
        test = getattr(obj, 'test', None)
        if not test:
            return None
        if obj.score > test.success_threshold:
            return 'green'
        if obj.score >= test.warning_threshold:
            return 'yellow'
        return 'red'
