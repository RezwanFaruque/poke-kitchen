from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .models import KitchenOrder


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
    )
    password = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'autocomplete': 'current-password'},
        ),
    )

    def clean_username(self):
        return self.cleaned_data['username'].strip().lower()


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autocomplete': 'email'}),
    )
    password1 = forms.CharField(
        label='Password',
        strip=False,
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'autocomplete': 'new-password'},
        ),
    )
    password2 = forms.CharField(
        label='Confirm password',
        strip=False,
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'autocomplete': 'new-password'},
        ),
    )

    class Meta:
        model = User
        fields = ('email',)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if len(email) > User._meta.get_field('username').max_length:
            raise forms.ValidationError('Email address must be 150 characters or fewer.')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            self.save_m2m()
        return user


class KitchenOrderForm(forms.ModelForm):
    class Meta:
        model = KitchenOrder
        fields = ['kitchen', 'customer_name', 'item_name', 'quantity', 'notes', 'status']
        widgets = {
            'kitchen': forms.Select(attrs={'class': 'form-select'}),
            'customer_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name'}),
            'item_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Item name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional details'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
        }
