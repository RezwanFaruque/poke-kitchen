from django import forms

from .models import KitchenOrder


class KitchenOrderForm(forms.ModelForm):
    class Meta:
        model = KitchenOrder
        fields = ['kitchen', 'customer_name', 'item_name', 'quantity', 'notes', 'status']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'customer_name': forms.TextInput(attrs={'placeholder': 'Customer name'}),
            'item_name': forms.TextInput(attrs={'placeholder': 'Item name'}),
        }
