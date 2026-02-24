from api.viewsets.base import BaseModelViewSet
from api.serializers import FeedbackSerializer, TaskReviewSerializer
from feedback.models import Feedback, TaskReview

ROLE_EMPLOYEE = 'EMPLOYEE'
ROLE_MANAGER = 'MANAGER'
ROLE_ANALYST = 'ANALYST'
ROLE_ADMIN = 'ADMIN'


class FeedbackViewSet(BaseModelViewSet):
    """Feedback on test results."""
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    schema_tags = ['Feedback']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    ordering_fields = ['id', 'created_at']
    filterset_fields = ['manager', 'test_result']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]:
            return Feedback.objects.all()
        return Feedback.objects.filter(test_result__user=user)

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)


class TaskReviewViewSet(BaseModelViewSet):
    """Reviews for task submissions."""
    queryset = TaskReview.objects.all()
    serializer_class = TaskReviewSerializer
    schema_tags = ['Task Reviews']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER]
    ordering_fields = ['id', 'created_at']
    filterset_fields = ['manager', 'task_submission']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]:
            return TaskReview.objects.all()
        return TaskReview.objects.filter(task_submission__assignment__user=user)

    def perform_create(self, serializer):
        serializer.save(manager=self.request.user)
