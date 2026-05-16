from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    def clean_text(self):
        text = self.cleaned_data['text'].strip()
        if len(text) < 10:
            raise forms.ValidationError('Отзыв должен содержать не менее 10 символов.')
        return text

    class Meta:
        model = Review
        fields = ['author_name', 'rating', 'text']
        widgets = {
            'author_name': forms.TextInput(attrs={
                'placeholder': 'Ваше имя',
                'maxlength': 80,
                'required': True,
            }),
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
