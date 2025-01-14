"""
sentry.web.forms
~~~~~~~~~~~~~~~~

:copyright: (c) 2010-2014 by the Sentry Team, see AUTHORS for more details.
:license: BSD, see LICENSE for more details.
"""
from __future__ import absolute_import

from django import forms
from django.utils.translation import ugettext_lazy as _

from sentry.models import User, Activity
from sentry.web.forms.fields import RadioFieldRenderer, ReadOnlyTextField


class BaseUserForm(forms.ModelForm):
    email = forms.EmailField()
    name = forms.CharField(required=True, label=_('Name'))


class ChangeUserForm(BaseUserForm):
    is_staff = forms.BooleanField(
        required=False,
        label=_('Admin'),
        help_text=_("Designates whether this user can perform administrative functions.")
    )
    is_superuser = forms.BooleanField(
        required=False,
        label=_('Superuser'),
        help_text=_(
            'Designates whether this user has all permissions without '
            'explicitly assigning them.'
        )
    )

    class Meta:
        fields = ('name', 'username', 'email', 'is_active', 'is_staff', 'is_superuser')
        model = User

    def __init__(self, *args, **kwargs):
        super(ChangeUserForm, self).__init__(*args, **kwargs)
        self.user = kwargs['instance']
        if self.user.is_managed:
            self.fields['username'] = ReadOnlyTextField(label="Username (managed)")

    def clean_username(self):
        if self.user.is_managed:
            return self.user.username
        return self.cleaned_data['username']


class RemoveUserForm(forms.Form):
    removal_type = forms.ChoiceField(
        choices=(
            ('1', _('Disable the account.')),
            ('2', _('Permanently remove the user and their data.')),
        ),
        widget=forms.RadioSelect(renderer=RadioFieldRenderer)
    )


class NewNoteForm(forms.Form):
    text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': '1',
                                     'placeholder': 'Type a note and press enter...'})
    )

    def save(self, group, user, event=None):
        activity = Activity.objects.create(
            group=group,
            project=group.project,
            type=Activity.NOTE,
            user=user,
            data=self.cleaned_data
        )
        activity.send_notification()

        return activity
