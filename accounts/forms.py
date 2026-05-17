from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile
from sales.models import Client, Employee, phone_validator, validate_adult


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    role = forms.ChoiceField(choices=UserProfile.ROLE_CHOICES, initial='client', label='Роль')
    last_name = forms.CharField(max_length=80, label='Фамилия')
    first_name = forms.CharField(max_length=80, label='Имя')
    middle_name = forms.CharField(max_length=80, required=False, label='Отчество')
    birth_date = forms.DateField(
        label='Дата рождения',
        validators=[validate_adult],
        widget=forms.DateInput(attrs={'type': 'date'}),
    )
    phone = forms.CharField(max_length=19, validators=[phone_validator], label='Телефон')
    city = forms.CharField(max_length=100, required=False, label='Город')
    address = forms.CharField(max_length=255, required=False, label='Адрес')
    position = forms.CharField(max_length=120, required=False, label='Должность')

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'role',
            'last_name',
            'first_name',
            'middle_name',
            'birth_date',
            'phone',
            'city',
            'address',
            'position',
            'password1',
            'password2',
        ]

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Пользователь с таким email уже существует.')
        if Client.objects.filter(email=email).exists() or Employee.objects.filter(email=email).exists():
            raise forms.ValidationError('Клиент или сотрудник с таким email уже существует.')
        return email

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if Client.objects.filter(phone=phone).exists() or Employee.objects.filter(phone=phone).exists():
            raise forms.ValidationError('Клиент или сотрудник с таким телефоном уже существует.')
        return phone

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')

        if role == 'client':
            if not cleaned_data.get('city'):
                self.add_error('city', 'Для клиента нужно указать город.')
            if not cleaned_data.get('address'):
                self.add_error('address', 'Для клиента нужно указать адрес.')

        if role == 'employee' and not cleaned_data.get('position'):
            self.add_error('position', 'Для сотрудника нужно указать должность.')

        return cleaned_data
