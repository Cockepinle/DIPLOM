from django import forms
from django.forms import inlineformset_factory

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
