from django import forms
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.forms import PasswordResetForm
from django.utils import timezone
import os

from .models import User, Specialty, Position


class UserRegisterForm(forms.ModelForm):
    email = forms.EmailField(label='Корпоративная почта')
    first_name = forms.CharField(label='Имя')
    last_name = forms.CharField(label='Фамилия')
    specialty = forms.ModelChoiceField(
        queryset=Specialty.objects.filter(is_active=True),
        label='Специальность',
        empty_label='Выберите специальность',
    )
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(is_active=True),
        label='Должность',
        required=False,
        empty_label='Выберите должность',
    )
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput,
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput,
    )

    class Meta:
        model = User
        fields = (
            'email',
            'first_name',
            'last_name',
            'specialty',
            'position',
        )

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if not email:
            return email
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Пользователь с такой почтой уже существует.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError('Пароли не совпадают.')
        if password1:
            validate_password(password1)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        email = (self.cleaned_data.get('email') or '').strip().lower()
        user.email = email
        user.role = User.Role.EMPLOYEE
        user.is_active = False
        user.registration_status = User.RegistrationStatus.PENDING
        user.registration_requested_at = timezone.now()
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    remove_avatar = forms.BooleanField(required=False, initial=False)

    class Meta:
        model = User
        fields = (
            'avatar',
            'first_name',
            'last_name',
            'department',
            'position',
        )
        widgets = {
            'avatar': forms.FileInput(attrs={'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in ('first_name', 'last_name', 'department', 'position'):
            field = self.fields.get(field_name)
            if field:
                field.disabled = True
        field = self.fields.get('avatar')
        if not field:
            return
        field.widget.attrs.setdefault('data-preview', 'image')
        avatar = getattr(self.instance, 'avatar', None)
        if avatar and getattr(avatar, 'url', None):
            field.widget.attrs['data-current-url'] = avatar.url
            field.widget.attrs['data-current-name'] = os.path.basename(getattr(avatar, 'name', '') or '') or 'Фото'
            field.widget.attrs['data-current-is-image'] = '1'


class ManagerStudentForm(forms.ModelForm):
    status = forms.TypedChoiceField(
        choices=(('1', 'Активен'), ('0', 'Заблокирован')),
        coerce=lambda value: value == '1',
        label='Статус',
        widget=forms.Select,
    )

    class Meta:
        model = User
        fields = (
            'first_name',
            'last_name',
            'department',
            'position',
            'specialty',
            'status',
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['specialty'].queryset = Specialty.objects.filter(is_active=True)
        self.fields['position'].queryset = Position.objects.filter(is_active=True)
        self.fields['status'].initial = self.instance.is_active

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = self.cleaned_data.get('status', True)
        if commit:
            user.save()
        return user


class ActiveUserPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        users = super().get_users(email)
        return [user for user in users if getattr(user, 'is_active', False)]
