from django import forms
from django.contrib.auth import get_user_model
import os

from .models import Course, Task, TaskSubmission, CourseMaterial
from tests.models import Test

User = get_user_model()


class RussianClearableFileInput(forms.ClearableFileInput):
    initial_text = 'Текущий файл'
    input_text = 'Изменить'
    clear_checkbox_label = 'Удалить'


class MultipleFileInput(forms.FileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        if not data:
            return []
        if not isinstance(data, (list, tuple)):
            data = [data]
        return [super().clean(item, initial) for item in data]


def _attach_file_preview(widget, value, *, preview='auto', is_image=None):
    if not widget:
        return
    attrs = widget.attrs
    attrs.setdefault('data-preview', preview)
    if value and getattr(value, 'url', None):
        attrs['data-current-url'] = value.url
        attrs['data-current-name'] = os.path.basename(getattr(value, 'name', '') or '') or 'Файл'
        if is_image is not None:
            attrs['data-current-is-image'] = '1' if is_image else '0'


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ('title', 'description', 'cover_image', 'specialty', 'is_active')
        widgets = {
            'cover_image': RussianClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _attach_file_preview(
            self.fields['cover_image'].widget,
            getattr(self.instance, 'cover_image', None),
            preview='image',
            is_image=True,
        )


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
            'attachment': RussianClearableFileInput(
                attrs={'accept': '.pdf,.doc,.docx,.odt,.rtf,.txt,.xlsx,.xls,.ppt,.pptx'}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _attach_file_preview(
            self.fields['attachment'].widget,
            getattr(self.instance, 'attachment', None),
            preview='file',
            is_image=False,
        )


class TaskAssignForm(forms.Form):
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

    def clean(self):
        cleaned_data = super().clean()
        users = cleaned_data.get('users')
        assign_all = cleaned_data.get('assign_all')
        if not assign_all and not users:
            self.add_error('users', 'Выберите сотрудников или отметьте "Выбрать всех".')
        return cleaned_data

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
        widgets = {
            'file': RussianClearableFileInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'file' in self.fields:
            _attach_file_preview(
                self.fields['file'].widget,
                getattr(self.instance, 'file', None),
                preview='file',
                is_image=False,
            )

    def clean(self):
        cleaned_data = super().clean()
        content = (cleaned_data.get('content') or '').strip()
        file = cleaned_data.get('file')
        if not content and not file:
            raise forms.ValidationError('Нужно добавить текст ответа или прикрепить файл.')
        return cleaned_data


class CourseMaterialForm(forms.ModelForm):
    files = MultipleFileField(
        required=False,
        label='Файлы',
        widget=MultipleFileInput(
            attrs={
                'multiple': True,
                'accept': '.pdf,.doc,.docx,.odt,.rtf,.txt,.xlsx,.xls,.ppt,.pptx',
            }
        ),
    )

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
            'file': RussianClearableFileInput(
                attrs={'accept': '.pdf,.doc,.docx,.odt,.rtf,.txt,.xlsx,.xls,.ppt,.pptx'}
            ),
            'image': RussianClearableFileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        course_qs = kwargs.pop('course_qs', None)
        tests_qs = kwargs.pop('tests_qs', None)
        super().__init__(*args, **kwargs)
        if course_qs is not None:
            self.fields['course'].queryset = course_qs
        if tests_qs is not None:
            self.fields['test'].queryset = tests_qs
        _attach_file_preview(
            self.fields['image'].widget,
            getattr(self.instance, 'image', None),
            preview='image',
            is_image=True,
        )
        _attach_file_preview(
            self.fields['file'].widget,
            getattr(self.instance, 'file', None),
            preview='file',
            is_image=False,
        )

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        test = cleaned_data.get('test')
        files = cleaned_data.get('files') or []
        material_type = cleaned_data.get('material_type')
        if test and course and test.course_id != course.id:
            self.add_error('test', 'Выбранный тест не относится к выбранному курсу.')
        if files and material_type != CourseMaterial.MaterialType.FILE:
            self.add_error('material_type', 'Загрузка нескольких файлов возможна только для материалов типа "Файл".')
        return cleaned_data
