from django import forms
from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'comment', 'image']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': 'Поделитесь подробностями о товаре...',
                'class': 'form-control'
            }),
            'rating': forms.RadioSelect(choices=[(i, str(i)) for i in range(1, 6)]),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            })
        }
