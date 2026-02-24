from api.viewsets.base import BaseModelViewSet
from api.serializers import TestResultSerializer
from results.models import TestResult

ROLE_EMPLOYEE = 'EMPLOYEE'
ROLE_MANAGER = 'MANAGER'
ROLE_ANALYST = 'ANALYST'
ROLE_ADMIN = 'ADMIN'


class TestResultViewSet(BaseModelViewSet):
    """Test results."""
    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer
    schema_tags = ['Results']
    read_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST, ROLE_EMPLOYEE]
    write_roles = [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]
    ordering_fields = ['id', 'completed_at', 'score']
    filterset_fields = ['user', 'test', 'passed', 'status']

    def get_queryset(self):
        user = self.request.user
        if getattr(user, 'is_superuser', False) or user.role in [ROLE_ADMIN, ROLE_MANAGER, ROLE_ANALYST]:
            return TestResult.objects.all()
        return TestResult.objects.filter(user=user)
