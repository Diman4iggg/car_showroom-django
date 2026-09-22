from django import forms

from .models import Review, Vacancy


class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = ['title', 'description', 'is_active']
        widgets = {
            'title': forms.TextInput(attrs={
                'maxlength': 150,
                'required': True,
                'aria-describedby': 'title-help',
                'autocomplete': 'off',
            }),
            'description': forms.Textarea(attrs={
                'rows': 6,
                'required': True,
            }),
        }


class ReviewForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if len(text) < 10:
            raise forms.ValidationError('Отзыв должен содержать не менее 10 символов.')
        return text

    def save(self, commit=True):
        review = super().save(commit=False)
        if self.user is not None:
            review.author_name = self.user.username
        if commit:
            review.save()
        return review

    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'required': True,
            }),
            'text': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Ваш отзыв',
                'maxlength': 1000,
                'minlength': 10,
                'required': True,
            }),
        }
