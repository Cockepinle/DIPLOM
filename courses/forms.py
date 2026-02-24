from django import forms
from django.contrib.auth import get_user_model

from .models import Course, Task, TaskSubmission, CourseMaterial
from tests.models import Test

User = get_user_model()


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'description', 'cover_image', 'specialty', 'is_active')
        widgets = {
            'cover_image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }


class CourseAssignForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label='Сотрудники',
        required=False,
    )
    assign_all = forms.BooleanField(
        required=False,
        label='Выбрать всех',
    )
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Срок прохождения'
    )

    def __init__(self, *args, **kwargs):
        users_qs = kwargs.pop('users_qs', User.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['users'].queryset = users_qs
        self.fields['users'].label_from_instance = self._user_label

    def _user_label(self, user):
        name = f"{user.last_name} {user.first_name}".strip() or user.email
        position = getattr(user, 'position', None)
        position_name = getattr(position, 'name', None)
        if position_name:
            return f"{name} · {position_name}"
        return name

    def clean(self):
        cleaned_data = super().clean()
        users = cleaned_data.get('users')
        assign_all = cleaned_data.get('assign_all')
        if not assign_all and not users:
            self.add_error('users', 'Выберите сотрудников или отметьте "Выбрать всех".')
        return cleaned_data


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = (
            'title',
            'description',
            'attachment',
            'criteria',
            'task_type',
            'max_score',
            'course',
            'due_date',
            'is_published',
        )
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'attachment': forms.ClearableFileInput(
                attrs={'accept': '.pdf,.doc,.docx,.odt,.rtf,.txt,.xlsx,.xls,.ppt,.pptx'}
            ),
        }


class TaskAssignForm(forms.Form):
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        label='Сотрудники'
    )
    due_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Срок выполнения'
    )
    priority = forms.IntegerField(
        min_value=1,
        max_value=5,
        initial=3,
        label='Приоритет (1-5)'
    )

    def __init__(self, *args, **kwargs):
        users_qs = kwargs.pop('users_qs', User.objects.none())
        super().__init__(*args, **kwargs)
        self.fields['users'].queryset = users_qs
        self.fields['users'].label_from_instance = self._user_label

    def _user_label(self, user):
        name = f"{user.last_name} {user.first_name}".strip() or user.email
        position = getattr(user, 'position', None)
        position_name = getattr(position, 'name', None)
        if position_name:
            return f"{name} ({user.email}) · {position_name}"
        return f"{name} ({user.email})"


class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ('content', 'file')

    def clean(self):
        cleaned_data = super().clean()
        content = (cleaned_data.get('content') or '').strip()
        file = cleaned_data.get('file')
        if not content and not file:
            raise forms.ValidationError('Нужно добавить текст ответа или прикрепить файл.')
        return cleaned_data


class CourseMaterialForm(forms.ModelForm):
    class Meta:
        model = CourseMaterial
        fields = (
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
        )
        widgets = {
            'accent_color': forms.TextInput(attrs={'type': 'color'}),
            'file': forms.ClearableFileInput(
                attrs={'accept': '.pdf,.doc,.docx,.odt,.rtf,.txt,.xlsx,.xls,.ppt,.pptx'}
            ),
            'image': forms.ClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        course_qs = kwargs.pop('course_qs', None)
        tests_qs = kwargs.pop('tests_qs', None)
        super().__init__(*args, **kwargs)
        if course_qs is not None:
            self.fields['course'].queryset = course_qs
        if tests_qs is not None:
            self.fields['test'].queryset = tests_qs

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        test = cleaned_data.get('test')
        if test and course and test.course_id != course.id:
            self.add_error('test', 'Выбранный тест не относится к выбранному курсу.')
        return cleaned_data
