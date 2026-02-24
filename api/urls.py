from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from api.auth import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    CustomTokenVerifyView,
    RegisterView,
)
from api.viewsets import (
    UserViewSet,
    SpecialtyViewSet,
    PositionViewSet,
    CompetencyViewSet,
    UserCompetencyViewSet,
    CompetencyAssessmentViewSet,
    CourseViewSet,
    CourseMaterialViewSet,
    EnrollmentViewSet,
    TaskViewSet,
    TaskAssignmentViewSet,
    TaskSubmissionViewSet,
    TestViewSet,
    QuestionViewSet,
    AnswerViewSet,
    MatchingPairViewSet,
    OrderingItemViewSet,
    TestResultViewSet,
    FeedbackViewSet,
    TaskReviewViewSet,
    AuditLogViewSet,
    TrainingEventViewSet,
    DashboardViewSet,
    ReportViewSet,
    ReportExportViewSet,
    BackupRecordViewSet,
)

router = DefaultRouter()

router.register('users', UserViewSet, basename='users')
router.register('specialties', SpecialtyViewSet, basename='specialties')
router.register('positions', PositionViewSet, basename='positions')
router.register('competencies', CompetencyViewSet, basename='competencies')
router.register('user-competencies', UserCompetencyViewSet, basename='user-competencies')
router.register('competency-assessments', CompetencyAssessmentViewSet, basename='competency-assessments')

router.register('courses', CourseViewSet, basename='courses')
router.register('course-materials', CourseMaterialViewSet, basename='course-materials')
router.register('enrollments', EnrollmentViewSet, basename='enrollments')
router.register('tasks', TaskViewSet, basename='tasks')
router.register('task-assignments', TaskAssignmentViewSet, basename='task-assignments')
router.register('task-submissions', TaskSubmissionViewSet, basename='task-submissions')

router.register('tests', TestViewSet, basename='tests')
router.register('questions', QuestionViewSet, basename='questions')
router.register('answers', AnswerViewSet, basename='answers')
router.register('matching-pairs', MatchingPairViewSet, basename='matching-pairs')
router.register('ordering-items', OrderingItemViewSet, basename='ordering-items')

router.register('results', TestResultViewSet, basename='results')

router.register('feedback', FeedbackViewSet, basename='feedback')
router.register('task-reviews', TaskReviewViewSet, basename='task-reviews')

router.register('audit-logs', AuditLogViewSet, basename='audit-logs')
router.register('training-events', TrainingEventViewSet, basename='training-events')
router.register('dashboards', DashboardViewSet, basename='dashboards')
router.register('reports', ReportViewSet, basename='reports')
router.register('report-exports', ReportExportViewSet, basename='report-exports')
router.register('backups', BackupRecordViewSet, basename='backups')

urlpatterns = [
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', CustomTokenVerifyView.as_view(), name='token_verify'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('', include(router.urls)),
]
