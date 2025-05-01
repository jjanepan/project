from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Review, Product, Routine, RoutineItem

# User signup form extending Django's built-in UserCreationForm
class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Require email field
    class Meta:
        model = User  # Use the User model
        fields = ("username", "email", "password1", "password2")  # Fields to display in the form

# Form for submitting a product review
class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review  # Use the Review model
        fields = ['rating', 'text']  # Include only rating and text fields
        widgets = {
            'rating': forms.RadioSelect(),  # Display rating as radio buttons (likely 1–5)
            'text': forms.Textarea(attrs={'rows': 4}),  # Show review text in a textarea with 4 rows
        }

# Form for creating or editing a Product
class ProductForm(forms.ModelForm):
    class Meta:
        model = Product  # Use the Product model
        exclude = ('owner',)  # Exclude the owner field (set it in the view instead)

# Form for creating or editing a Routine
class RoutineForm(forms.ModelForm):
    class Meta:
        model = Routine  # Use the Routine model
        exclude = ('owner',)  # Exclude the owner field (set it in the view instead)

# Form for adding/editing items in a Routine
class RoutineItemForm(forms.ModelForm):
    class Meta:
        model = RoutineItem  # Use the RoutineItem model
        fields = ['product', 'step_order', 'notes']  # Include these fields in_]()
