from django import forms
from django.forms import inlineformset_factory
import os

from .models import Test, Question, Answer, MatchingPair, OrderingItem


class TestForm(forms.ModelForm):
    class Meta:
        model = Test
        fields = (
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
        )
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned = super().clean()
        warning = cleaned.get('warning_threshold')
        success = cleaned.get('success_threshold')
        if warning is not None and success is not None and warning >= success:
            self.add_error(
                'success_threshold',
                'Порог для зеленого должен быть больше порога для желтого.',
            )
        return cleaned


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('type', 'text', 'points', 'image')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields.get('image')
        if not field:
            return
        field.widget.attrs.setdefault('data-preview', 'auto')
        image = getattr(self.instance, 'image', None)
        if image and getattr(image, 'url', None):
            field.widget.attrs['data-current-url'] = image.url
            field.widget.attrs['data-current-name'] = os.path.basename(getattr(image, 'name', '') or '') or 'Файл'
            is_img = False
            if hasattr(self.instance, 'is_image'):
                try:
                    is_img = bool(self.instance.is_image())
                except Exception:
                    is_img = False
            field.widget.attrs['data-current-is-image'] = '1' if is_img else '0'


AnswerFormSet = inlineformset_factory(
    Question,
    Answer,
    fields=('text', 'is_correct'),
    extra=4,
    min_num=2,
    validate_min=True,
)


MatchingPairFormSet = inlineformset_factory(
    Question,
    MatchingPair,
    fields=('left_text', 'right_text'),
    extra=2,
    min_num=1,
    validate_min=True,
)


OrderingItemFormSet = inlineformset_factory(
    Question,
    OrderingItem,
    fields=('text', 'position'),
    extra=2,
    min_num=2,
    validate_min=True,
)
