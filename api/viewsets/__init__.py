from .users import (
    UserViewSet,
    SpecialtyViewSet,
    PositionViewSet,
    CompetencyViewSet,
    UserCompetencyViewSet,
    CompetencyAssessmentViewSet,
)
from .courses import (
    CourseViewSet,
    CourseMaterialViewSet,
    EnrollmentViewSet,
    TaskViewSet,
    TaskAssignmentViewSet,
    TaskSubmissionViewSet,
)
from .tests import (
    TestViewSet,
    QuestionViewSet,
    AnswerViewSet,
    MatchingPairViewSet,
    OrderingItemViewSet,
)
from .results import TestResultViewSet
from .feedback import FeedbackViewSet, TaskReviewViewSet
from .analytics import (
    AuditLogViewSet,
    TrainingEventViewSet,
    DashboardViewSet,
    ReportViewSet,
    ReportExportViewSet,
    BackupRecordViewSet,
)

__all__ = [
    'UserViewSet',
    'SpecialtyViewSet',
    'PositionViewSet',
    'CompetencyViewSet',
    'UserCompetencyViewSet',
    'CompetencyAssessmentViewSet',
    'CourseViewSet',
    'CourseMaterialViewSet',
    'EnrollmentViewSet',
    'TaskViewSet',
    'TaskAssignmentViewSet',
    'TaskSubmissionViewSet',
    'TestViewSet',
    'QuestionViewSet',
    'AnswerViewSet',
    'MatchingPairViewSet',
    'OrderingItemViewSet',
    'TestResultViewSet',
    'FeedbackViewSet',
    'TaskReviewViewSet',
    'AuditLogViewSet',
    'TrainingEventViewSet',
    'DashboardViewSet',
    'ReportViewSet',
    'ReportExportViewSet',
    'BackupRecordViewSet',
]
