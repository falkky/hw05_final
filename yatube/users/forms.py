from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (AuthenticationForm,
                                       PasswordResetForm,
                                       UserCreationForm
                                       )

User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class LoginForm(AuthenticationForm):
    class Meta:
        model = User
        fields = ('username', 'password')


class PasswordResetForm(PasswordResetForm):
    class Meta:
        model = User
        fields = ('username', 'password')
