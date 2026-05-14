from django.contrib import admin
from .models import Competency, CompetencyAssessment, Specialty, Position, User, UserCompetency


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        'last_name',
        'first_name',
        'email',
        'role',
        'department',
        'position',
        'specialty',
        'is_active',
    )
    list_filter = ('role', 'department', 'position', 'specialty', 'is_active', 'is_staff')
    search_fields = ('last_name', 'email', 'position__name')
    readonly_fields = ('email', 'password')
    fields = (
        'email',
        'password',
        'first_name',
        'last_name',
        'role',
        'department',
        'position',
        'specialty',
        'avatar',
        'registration_status',
        'registration_requested_at',
        'registration_reviewed_at',
        'registration_reviewed_by',
        'registration_review_comment',
        'is_active',
        'is_staff',
        'is_superuser',
        'groups',
        'user_permissions',
        'last_login',
        'date_joined',
    )


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Competency)
class CompetencyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)


@admin.register(UserCompetency)
class UserCompetencyAdmin(admin.ModelAdmin):
    list_display = ('user', 'competency', 'level', 'source', 'updated_at')
    list_filter = ('source',)
    search_fields = ('user__email', 'competency__name')


@admin.register(CompetencyAssessment)
class CompetencyAssessmentAdmin(admin.ModelAdmin):
    list_display = ('user', 'competency', 'level', 'assessor', 'assessed_at')
    list_filter = ('competency',)
    search_fields = ('user__email', 'competency__name', 'assessor__email')
