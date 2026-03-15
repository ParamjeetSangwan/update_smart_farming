# products/forms.py
from django import forms
from marketplace.models import Tool, Pesticide

class ToolForm(forms.ModelForm):
    class Meta:
        model = Tool
        fields = ['name', 'description', 'price', 'category', 'image']

class PesticideForm(forms.ModelForm):
    class Meta:
        model = Pesticide
        fields = ['name', 'description', 'price', 'image']
