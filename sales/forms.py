from datetime import date

from django import forms


class PaymentForm(forms.Form):
    cardholder_name = forms.CharField(max_length=100, label='Имя владельца карты')
    card_number = forms.RegexField(
        regex=r'^\d{16}$',
        label='Номер карты',
        error_messages={'invalid': 'Введите ровно 16 цифр без пробелов.'},
    )
    expiry_month = forms.ChoiceField(
        choices=[(f'{month:02d}', f'{month:02d}') for month in range(1, 13)],
        label='Месяц окончания',
    )
    expiry_year = forms.ChoiceField(
        choices=[(str(year), str(year)) for year in range(date.today().year, date.today().year + 11)],
        label='Год окончания',
    )
    cvv = forms.RegexField(
        regex=r'^\d{3}$',
        label='CVV',
        error_messages={'invalid': 'CVV должен состоять из трёх цифр.'},
    )
    agreement = forms.BooleanField(label='Я подтверждаю оплату демонстрационного заказа')

    def clean(self):
        cleaned_data = super().clean()
        month = cleaned_data.get('expiry_month')
        year = cleaned_data.get('expiry_year')
        if month and year:
            today = date.today()
            if (int(year), int(month)) < (today.year, today.month):
                raise forms.ValidationError('Срок действия карты уже истёк.')
        return cleaned_data
