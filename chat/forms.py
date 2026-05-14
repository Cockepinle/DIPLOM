from django import forms
from django.conf import settings


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


def _get_max_upload_bytes() -> int:
    mb = int(getattr(settings, 'CHAT_MAX_UPLOAD_MB', 20) or 20)
    return mb * 1024 * 1024


def _get_max_files() -> int:
    return int(getattr(settings, 'CHAT_MAX_FILES_PER_MESSAGE', 5) or 5)


class DirectMessageForm(forms.Form):
    text = forms.CharField(
        label='',
        required=False,
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Сообщение…'}),
        max_length=5000,
    )
    files = MultipleFileField(
        label='',
        required=False,
        widget=MultipleFileInput(attrs={'multiple': True}),
    )

    def clean(self):
        cleaned = super().clean()
        text = (cleaned.get('text') or '').strip()
        files = self.files.getlist('files') if hasattr(self, 'files') else []

        if not text and not files:
            raise forms.ValidationError('Введите сообщение или прикрепите файл.')

        if files:
            max_files = _get_max_files()
            if len(files) > max_files:
                raise forms.ValidationError(f'Можно прикрепить не более {max_files} файлов.')

            max_bytes = _get_max_upload_bytes()
            for f in files:
                if getattr(f, 'size', 0) and f.size > max_bytes:
                    mb = max_bytes // (1024 * 1024)
                    raise forms.ValidationError(f'Файл "{f.name}" слишком большой. Максимум {mb} МБ.')

        cleaned['text'] = text
        return cleaned
