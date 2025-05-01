from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Review
from .models import Product, Routine, RoutineItem

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta:
        model = User
        fields = ("username","email","password1","password2")
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'text']
        widgets = {
            'rating': forms.RadioSelect(),  # renders 1–5 as radio buttons
            'text': forms.Textarea(attrs={'rows':4}),
        }

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        # exclude `owner` because we’ll set it in the view
        exclude = ('owner',)

class RoutineForm(forms.ModelForm):
    class Meta:
        model = Routine
        exclude = ('owner',)

class RoutineItemForm(forms.ModelForm):
    class Meta:
        model = RoutineItem
        fields = ['product', 'step_order', 'notes']