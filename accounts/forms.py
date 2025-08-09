from django import forms
from .models import CustomUser, OperationsRecord, SalesRecord, Finance,  SpecialSale


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
        fields = ['bags_produced', 'stereo_received', 'bad_stereo', 'stereo_used','cone',
                  'packaging_bags', 'packaging_bags_used','comments','diesel_received', 'diesel_used']



class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Finance
        fields = ['expense_type','custom_expense_name', 'amount', 'receipt', 'comments']



class SalesForm(forms.ModelForm):
    class Meta:
        model = SalesRecord
        fields = ['bags_sold','applied_discount', 'keystone', 'zenith', 'moniepoint', 'cash','to_umuahia', 'law_enforcement','rebagged','lost_to_rebagging', 'damaged', 'comments']



class SpecialSaleForm(forms.ModelForm):
    class Meta:
        model = SpecialSale
        fields = ['bags_sold', 'keystone','applied_discount', 'zenith', 'moniepoint', 'cash', 'comments']
