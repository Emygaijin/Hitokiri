from django import forms
from .models import CustomUser, OperationsRecord, SalesRecord, Finance


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'name', 'surname', 'date_of_birth', 'phone_number',
            'email', 'date_joined', 'status', 'date_disengaged', 'role',
            'password', 'cv', 'photo'  # Added fields
        ]
        widgets = {
            'password': forms.PasswordInput(),
        }




class BagsForm(forms.ModelForm):
    class Meta:
        model = OperationsRecord
        fields = ['bags_produced', 'bags_returned', 'bags_pushed_to_sales','comments']



class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Finance
        fields = ['expense_title', 'amount', 'receipt', 'comments']



class SalesForm(forms.ModelForm):
    class Meta:
        model = SalesRecord
        fields = ['bags_sold', 'bags_returned', 'bags_received_from_production','applied_discount', 'keystone', 'zenith', 'moniepoint', 'cash', 'comments']
