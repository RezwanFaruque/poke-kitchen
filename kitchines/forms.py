from django import forms

from .models import KitchenOrder


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
