from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class StockSearchForm(forms.Form):
    ticker = forms.CharField(label='Stock Ticker', max_length=25, required=False)

class NewUserForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('label_suffix', '')
        super(NewUserForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super(NewUserForm, self).save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

    def as_p(self):
        return self._html_output(
            normal_row = u'<br>%(html_class_attr)s%(label)s<br> <i>%(field)s%(help_text)s</i><br>',
            error_row = u'%s',
            row_ender = '</p>',
            help_text_html = u'<br><span class="helptext">%s</span>',
            errors_on_separate_row = True)
