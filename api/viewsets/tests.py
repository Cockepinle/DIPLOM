from django.db import transaction
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response

from api.viewsets.base import BaseModelViewSet
from api.serializers import (
    TestSerializer,
    QuestionSerializer,
    AnswerSerializer,
    MatchingPairSerializer,
    OrderingItemSerializer,
    TestSubmissionSerializer,
    TestResultSerializer,
)
from results.models import TestResult, TestAnswer
from feedback.models import Feedback
from tests.models import (
    Test,
    Question,
    Answer,
    MatchingPair,
    OrderingItem,
    QUESTION_TYPE_SINGLE,
    QUESTION_TYPE_MULTI,
    QUESTION_TYPE_MATCHING,
    QUESTION_TYPE_ORDERING,
    QUESTION_TYPE_SHORT,
    QUESTION_TYPE_LONG,
    MANUAL_QUESTION_TYPES,
)

ROLE_EMPLOYEE = 'EMPLOYEE'
ROLE_MANAGER = 'MANAGER'
ROLE_ANALYST = 'ANALYST'
ROLE_ADMIN = 'ADMIN'


class TestViewSet(BaseModelViewSet):
    queryset = Test.objects.all()
    serializer_class = TestSerializer
    schema_tags = ['Tests']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['title', 'description']
    ordering_fields = ['id', 'title', 'created_at', 'due_date']
    filterset_fields = ['course', 'is_published', 'created_by']

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def get_permissions(self):
        if getattr(self, 'action', None) == 'submit':
            self.write_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
        return super().get_permissions()

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        test = self.get_object()
        serializer = TestSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers_data = serializer.validated_data.get('answers', [])

        if not test.is_published and request.user.role == ROLE_EMPLOYEE:
            return Response({'detail': 'Test is not published.'}, status=status.HTTP_403_FORBIDDEN)

        total_questions = test.questions.count()
        if total_questions == 0:
            return Response({'detail': 'Test has no questions.'}, status=status.HTTP_400_BAD_REQUEST)

        submission_map = {}
        for item in answers_data:
            question_id = item['question']
            if question_id in submission_map:
                return Response(
                    {'answers': 'Only one submission is allowed per question.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            submission_map[question_id] = item

        questions = list(test.questions.all())
        question_by_id = {question.id: question for question in questions}
        question_points = {question.id: question.points for question in questions}
        question_ids = set(question_by_id.keys())
        if any(qid not in question_ids for qid in submission_map.keys()):
            return Response(
                {'answers': 'Answers contain questions outside this test.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        total_points = sum(question_points.values())
        if total_points <= 0:
            return Response(
                {'detail': 'Test has invalid question points.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        choice_question_ids = [
            qid
            for qid, question in question_by_id.items()
            if question.type in {QUESTION_TYPE_SINGLE, QUESTION_TYPE_MULTI}
        ]
        answers_by_id = {}
        correct_answers_by_question = {}
        if choice_question_ids:
            answers_qs = Answer.objects.filter(
                question_id__in=choice_question_ids,
            ).values('id', 'question_id', 'is_correct')
            for row in answers_qs:
                answers_by_id[row['id']] = row
                if row['is_correct']:
                    correct_answers_by_question.setdefault(row['question_id'], set()).add(row['id'])

        matching_question_ids = [
            qid
            for qid, question in question_by_id.items()
            if question.type == QUESTION_TYPE_MATCHING
        ]
        matching_pair_ids_by_question = {qid: set() for qid in matching_question_ids}
        if matching_question_ids:
            for row in MatchingPair.objects.filter(
                question_id__in=matching_question_ids
            ).values('id', 'question_id'):
                matching_pair_ids_by_question[row['question_id']].add(row['id'])

        ordering_question_ids = [
            qid
            for qid, question in question_by_id.items()
            if question.type == QUESTION_TYPE_ORDERING
        ]
        ordering_ids_by_question = {qid: set() for qid in ordering_question_ids}
        ordering_correct_order_by_question = {qid: [] for qid in ordering_question_ids}
        if ordering_question_ids:
            ordering_items = OrderingItem.objects.filter(
                question_id__in=ordering_question_ids
            ).values('id', 'question_id', 'position').order_by('position', 'id')
            for row in ordering_items:
                ordering_ids_by_question[row['question_id']].add(row['id'])
                ordering_correct_order_by_question[row['question_id']].append(row['id'])

        manual_exists = any(
            question.type in MANUAL_QUESTION_TYPES for question in questions
        )
        expected_evaluation = (
            Test.EvaluationType.MANUAL if manual_exists else Test.EvaluationType.AUTO
        )
        if test.evaluation_type != expected_evaluation:
            Test.objects.filter(pk=test.pk).update(evaluation_type=expected_evaluation)
            test.evaluation_type = expected_evaluation
        declined_result = (
            TestResult.objects.filter(
                user=request.user,
                test=test,
                status=TestResult.Status.DECLINED,
            )
            .order_by('-completed_at', '-id')
            .first()
        )
        if declined_result:
            return Response(
                {'detail': 'Retake was declined for this test.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            returned_result = None
            reuse_returned = False
            if not test.retake_requires_new_attempt:
                returned_result = (
                    TestResult.objects.filter(
                        user=request.user,
                        test=test,
                        status=TestResult.Status.RETURNED,
                    )
                    .order_by('-completed_at', '-id')
                    .first()
                )
                reuse_returned = returned_result is not None

            if reuse_returned:
                attempt_number = returned_result.attempt_number
            else:
                attempts_used = TestResult.objects.filter(
                    user=request.user,
                    test=test,
                ).count()
                attempt_limit = test.attempts
                if attempts_used >= attempt_limit:
                    return Response(
                        {'detail': 'Attempt limit reached.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                attempt_number = attempts_used + 1

            test_answers = []
            correct_points = 0
            for question_id, submission in submission_map.items():
                question = question_by_id.get(question_id)
                if not question:
                    continue
                question_type = question.type
                points = question_points.get(question_id, 0)

                if question_type == QUESTION_TYPE_SINGLE:
                    answer_id = submission.get('answer')
                    answers_list = submission.get('answers') or []
                    if answer_id is None and answers_list:
                        if len(answers_list) != 1:
                            return Response(
                                {'answers': 'Only one answer is allowed for single-choice questions.'},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        answer_id = answers_list[0]
                    if answer_id is None:
                        return Response(
                            {'answers': f'Answer is required for question {question_id}.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    answer_row = answers_by_id.get(answer_id)
                    if not answer_row or answer_row['question_id'] != question_id:
                        return Response(
                            {'answers': 'Answer does not match question.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    correct_ids = correct_answers_by_question.get(question_id, set())
                    if len(correct_ids) != 1:
                        return Response(
                            {'answers': f'Question {question_id} must have exactly one correct answer.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    is_correct = bool(answer_row['is_correct'])
                    if is_correct:
                        correct_points += points
                    test_answers.append(
                        TestAnswer(
                            question_id=question_id,
                            answer_id=answer_id,
                            is_correct=is_correct,
                        )
                    )
                elif question_type == QUESTION_TYPE_MULTI:
                    selected_ids = submission.get('answers')
                    if selected_ids is None:
                        answer_id = submission.get('answer')
                        selected_ids = [answer_id] if answer_id is not None else []
                    if not isinstance(selected_ids, list):
                        return Response(
                            {'answers': 'Answers must be a list for multiple-choice questions.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if len(selected_ids) != len(set(selected_ids)):
                        return Response(
                            {'answers': 'Duplicate answers are not allowed.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    for answer_id in selected_ids:
                        answer_row = answers_by_id.get(answer_id)
                        if not answer_row or answer_row['question_id'] != question_id:
                            return Response(
                                {'answers': 'Answer does not match question.'},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    correct_ids = correct_answers_by_question.get(question_id, set())
                    if not correct_ids:
                        return Response(
                            {'answers': f'Question {question_id} must have at least one correct answer.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    is_correct = set(selected_ids) == correct_ids
                    if is_correct:
                        correct_points += points
                    test_answers.append(
                        TestAnswer(
                            question_id=question_id,
                            answer_data={'answers': selected_ids},
                            is_correct=is_correct,
                        )
                    )
                elif question_type == QUESTION_TYPE_MATCHING:
                    matches = submission.get('matches') or []
                    if not isinstance(matches, list):
                        return Response(
                            {'answers': 'Matches must be a list.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    pair_ids = matching_pair_ids_by_question.get(question_id, set())
                    if not pair_ids:
                        return Response(
                            {'answers': f'Question {question_id} must have matching pairs.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    seen_left_ids = set()
                    mapping = []
                    for match in matches:
                        left_id = match.get('left_id')
                        right_id = match.get('right_id')
                        if left_id is None or right_id is None:
                            return Response(
                                {'answers': 'Each match must include left_id and right_id.'},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        if left_id in seen_left_ids:
                            return Response(
                                {'answers': 'Duplicate left_id in matches.'},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        if left_id not in pair_ids or right_id not in pair_ids:
                            return Response(
                                {'answers': 'Match items are invalid.'},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        seen_left_ids.add(left_id)
                        mapping.append({'left_id': left_id, 'right_id': right_id})
                    is_correct = (
                        set(seen_left_ids) == pair_ids
                        and all(item['left_id'] == item['right_id'] for item in mapping)
                    )
                    if is_correct:
                        correct_points += points
                    test_answers.append(
                        TestAnswer(
                            question_id=question_id,
                            answer_data={'matches': mapping},
                            is_correct=is_correct,
                        )
                    )
                elif question_type == QUESTION_TYPE_ORDERING:
                    order = submission.get('order') or []
                    if not isinstance(order, list):
                        return Response(
                            {'answers': 'Order must be a list.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    ordering_ids = ordering_ids_by_question.get(question_id, set())
                    if not ordering_ids:
                        return Response(
                            {'answers': f'Question {question_id} must have ordering items.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    if len(order) != len(set(order)):
                        return Response(
                            {'answers': 'Duplicate items are not allowed in ordering.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    for item_id in order:
                        if item_id not in ordering_ids:
                            return Response(
                                {'answers': 'Ordering items are invalid.'},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    correct_order = ordering_correct_order_by_question.get(question_id, [])
                    is_correct = order == correct_order
                    if is_correct:
                        correct_points += points
                    test_answers.append(
                        TestAnswer(
                            question_id=question_id,
                            answer_data={'order': order},
                            is_correct=is_correct,
                        )
                    )
                elif question_type in {QUESTION_TYPE_SHORT, QUESTION_TYPE_LONG}:
                    text = submission.get('text')
                    if text is None:
                        text = ''
                    test_answers.append(
                        TestAnswer(
                            question_id=question_id,
                            answer_text=text,
                            is_correct=None,
                        )
                    )
                else:
                    return Response(
                        {'answers': 'Unsupported question type.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            score = None
            passed = None
            if not manual_exists:
                score = int(round((correct_points / total_points) * 100))
                passed = score >= test.passing_score
                status_value = (
                    TestResult.Status.PASSED if passed else TestResult.Status.FAILED
                )
            else:
                status_value = TestResult.Status.UNDER_REVIEW

            if reuse_returned:
                result = returned_result
                result.score = score
                result.passed = passed
                result.status = status_value
                result.attempt_number = attempt_number
                result.save(update_fields=['score', 'passed', 'status', 'attempt_number'])
                TestAnswer.objects.filter(test_result=result).delete()
                Feedback.objects.filter(test_result=result).delete()
            else:
                result = TestResult.objects.create(
                    user=request.user,
                    test=test,
                    score=score,
                    passed=passed,
                    status=status_value,
                    attempt_number=attempt_number,
                )

            if test_answers:
                for answer in test_answers:
                    answer.test_result = result
                TestAnswer.objects.bulk_create(test_answers)

        return Response(
            TestResultSerializer(result).data,
            status=status.HTTP_201_CREATED,
        )


class QuestionViewSet(BaseModelViewSet):
    """Questions for tests."""
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    schema_tags = ['Questions']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['text']
    ordering_fields = ['id']
    filterset_fields = ['test']


class AnswerViewSet(BaseModelViewSet):
    """Answers for questions."""
    queryset = Answer.objects.all()
    serializer_class = AnswerSerializer
    schema_tags = ['Answers']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['text']
    ordering_fields = ['id']
    filterset_fields = ['question', 'is_correct']


class MatchingPairViewSet(BaseModelViewSet):
    """Matching pairs for questions."""
    queryset = MatchingPair.objects.all()
    serializer_class = MatchingPairSerializer
    schema_tags = ['Matching']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['left_text', 'right_text']
    ordering_fields = ['id', 'order']
    filterset_fields = ['question']


class OrderingItemViewSet(BaseModelViewSet):
    """Ordering items for questions."""
    queryset = OrderingItem.objects.all()
    serializer_class = OrderingItemSerializer
    schema_tags = ['Ordering']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    search_fields = ['text']
    ordering_fields = ['id', 'position']
    filterset_fields = ['question']
