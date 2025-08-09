from django.urls import path
from django.contrib.auth.views import LogoutView
from .views import (
    register,
    custom_login,
    dashboard,
    operations_dashboard,
    add_bags_record,
    add_expense_record,
    landing_page,
    sales_dashboard,
    add_sales_record,
    supervisor_dashboard,  # Import the admin dashboard view
    staff_info,
    finance_office,
    query_records,
    receipt_list,
    auto_logout,
    add_special_sales_record,
    query_expenses,
    edit_sales_record,
    edit_operations_record,
    edit_finance_record,
)

urlpatterns = [
    path('', landing_page, name='landing_page'),  # Main landing page
    path('register/', register, name='register'),  # User registration
    path('login/', custom_login, name='login'),  # User login
    path('logout/', auto_logout, name='logout'),
    path('logout/', LogoutView.as_view(next_page='landing_page'), name='logout'),
    path('dashboard/', dashboard, name='dashboard'),  # General user dashboard
    path('operations/', operations_dashboard, name='operations_dashboard'),  # Operations manager dashboard
    path('operations/add-bags/', add_bags_record, name='add_bags_record'),  # Add bags record
    path('finance_office/', finance_office, name='finance'), #finance dashboard
    path('operations/add-expense/', add_expense_record, name='add_expense_record'),  # Add expense record
    path('sales/dashboard/', sales_dashboard, name='sales_dashboard'),  # Sales dashboard
    path('sales/add/', add_sales_record, name='add_sales_record'),  # Add sales record
    path('sales/add/', add_special_sales_record, name='add_special_sales_record'),  # Add special_sales record
    path('supervisor/dashboard/', supervisor_dashboard, name='supervisor_dashboard'),  # Admin dashboard
    path('staff_info/<str:name>', staff_info, name='staff'),
    path('query/', query_records, name='query_records'),
    path('receipts/', receipt_list, name='receipt_list'),
    path('query-expenses/', query_expenses, name='query_expenses'),
    path('edit-sales-record/<int:pk>/', edit_sales_record, name='edit_sales_record'),
    path('edit-operations-record/<int:pk>/', edit_operations_record, name='edit_operations_record'),
    path('edit-finance/<int:pk>/', edit_finance_record, name='edit_finance_record'),


]
