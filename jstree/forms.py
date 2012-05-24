# -*- coding: utf-8 -*-
from django import forms

class GetSubTreeForm(forms.Form):
    parent = forms.ModelChoiceField(required=False, queryset=None)

class AddNodeForm(forms.ModelForm):
    class Meta:
        fields = ('parent', 'name',)

class MoveNodeForm(forms.Form):
    POSITION_CHOICES = [
        ('left', 'left'),
        ('right', 'right'),
        ('last-child', 'last-child'),
        ('first-child', 'first-child'),
    ]
    node = forms.ModelChoiceField(queryset=None)
    target = forms.ModelChoiceField(queryset=None)
    position = forms.ChoiceField(choices=POSITION_CHOICES)