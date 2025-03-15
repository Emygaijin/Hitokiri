from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, BagsForm, ExpenseForm, SalesForm
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncDay
from .models import OperationsRecord, CustomUser, SalesRecord, Finance
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.utils.timezone import now



# Signal to invalidate previous sessions when a new login occurs
@receiver(user_logged_in)
def invalidate_previous_sessions(sender, request, user, **kwargs):
    # Get all active sessions for the current user
    active_sessions = Session.objects.filter(expire_date__gte=now())
    for session in active_sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user.id) and session.session_key != request.session.session_key:
            # Delete previous sessions
            session.delete()



# Landing page (Main page)
def landing_page(request):
    return render(request, 'accounts/landing_page.html')


def auto_logout(request):
    logout(request)
    return redirect('login')


# Registration view
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST, request.FILES)  # Handle file uploads
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])  # Set password securely
            user.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


# Custom login view with operations manager redirection
def custom_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_approved:
                login(request, user)
                # Redirect to appropriate dashboard based on role
                if user.role == 'Operations Manager':
                    return redirect('operations_dashboard')
                elif user.role == 'Sales':  # Restrict to sales dashboard for sales role
                    return redirect('sales_dashboard')
                elif user.role == 'Supervisor':
                    return redirect('supervisor_dashboard')
                elif user.role == 'Finance':
                    return redirect('finance')

            else:
                return render(request, 'accounts/login.html', {'error': 'User not approved yet.'})
        else:
            return render(request, 'accounts/login.html', {'error': 'Invalid credentials.'})
    return render(request, 'accounts/login.html')



# General user dashboard
@login_required
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


# Operations manager dashboard
@login_required
def operations_dashboard(request):
    if request.user.role != 'Operations Manager':
        return redirect('landing_page')  # Restrict access for non-operations managers
    records = OperationsRecord.objects.all().order_by('-date_produced')
    return render(request, 'accounts/operations_dashboard.html', {'records': records})


# Add bags record view
@login_required
def add_bags_record(request):
    if request.user.role != 'Operations Manager':
        return redirect('landing_page')  # Restrict access for non-operations managers
    if request.method == 'POST':
        form = BagsForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('operations_dashboard')
    else:
        form = BagsForm()
    return render(request, 'accounts/add_bags.html', {'form': form})


# Add expense record view
@login_required
def add_expense_record(request):
    if request.user.role != 'Finance':
        return redirect('landing_page')  # Restrict access for non-operations managers
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('finance')
    else:
        form = ExpenseForm()
    return render(request, 'accounts/add_expense.html', {'form': form})


@login_required
def finance_office(request):
    operations_records = OperationsRecord.objects.all().order_by('-date_produced')[:5]
    sales_records = SalesRecord.objects.all().order_by('-date_of_sale')[:5]

    finance_records = Finance.objects.all()

    # Default values for start_date and end_date
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if start_date and end_date:
        try:
            # Convert string dates to datetime objects
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()

            # Filter expenses by date range
            finance_records = Finance.objects.filter(date_of_expense__range=[start_date_obj, end_date_obj])

        except ValueError:
            # If there's an invalid date format, reset to default empty values
            start_date = ''
            end_date = ''

    # Calculate total expenses
    total_expenses = finance_records.aggregate(Sum('amount'))['amount__sum'] or 0

    return render(request, 'accounts/finance.html', {
        'operations_records': operations_records,
        'sales_records': sales_records,
        'finance_records': finance_records,
        'total_expenses': total_expenses,
        'start_date': start_date,  # Pass as string
        'end_date': end_date  # Pass as string
    })



# Sales manager dashboard
@login_required
def sales_dashboard(request):
    staff_info = CustomUser.objects.all()
    sales_records = SalesRecord.objects.all().order_by('-date_of_sale')[:25]
    if request.user.role != 'Sales':
        return redirect('landing_page')  # Restrict access for non-Sales
    return render(request, 'accounts/sales_dashboard.html', {'sales_records': sales_records, 'staff_info':staff_info})


# Add sales record view
@login_required()
def add_sales_record(request):
    if request.user.role != 'Sales':
        return redirect('dashboard')  # Restrict access for non-Sales
    if request.method == 'POST':
        form = SalesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales_dashboard')
    else:
        form = SalesForm()
    return render(request, 'accounts/add_sales_records.html', {'form': form})




@login_required
def supervisor_dashboard(request):
    # Total staff
    total_staff = CustomUser.objects.count()
    finance_records = Finance.objects.all().order_by('-date_of_expense')[:5]



    # Total sales

    total_sales = SalesRecord.objects.aggregate(total_bags_sold=Sum('bags_sold'))['total_bags_sold'] or 0

    grand_total = SalesRecord.objects.aggregate(total_cash=Sum('total'))['total_cash'] or 0

    # Total operations (e.g., bags produced)
    total_bags_produced = OperationsRecord.objects.aggregate(total_bags=Sum('bags_produced'))['total_bags'] or 0
    total_expenses = Finance.objects.aggregate(all_expenses=Sum('amount'))['all_expenses'] or 0

    #Calculate net
    net = grand_total - total_expenses

    # Staff information
    staff_info = CustomUser.objects.all()

    # Filter parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    min_bags_produced = request.GET.get('min_bags_produced')
    max_bags_produced = request.GET.get('max_bags_produced')
    min_bags_sold = request.GET.get('min_bags_sold')
    max_bags_sold = request.GET.get('max_bags_sold')


    # Calculate default start date (30 days ago)
    default_start_date = datetime.now() - timedelta(days=30)
    start_date = start_date or default_start_date.strftime('%Y-%m-%d')

    # Filter records
    operations_filter = Q()
    sales_filter = Q()




    if start_date and end_date:
        operations_filter &= Q(date_produced__range=[start_date, end_date])
        sales_filter &= Q(date_of_sale__range=[start_date, end_date])
    if min_bags_produced:
        operations_filter &= Q(bags_produced__gte=min_bags_produced)
    if max_bags_produced:
        operations_filter &= Q(bags_produced__lte=max_bags_produced)
    if min_bags_sold:
        sales_filter &= Q(bags_sold__gte=min_bags_sold)
    if max_bags_sold:
        sales_filter &= Q(bags_sold__lte=max_bags_sold)

    operations_records = OperationsRecord.objects.all().order_by('-date_produced')[:5]
    sales_records = SalesRecord.objects.all().order_by('-date_of_sale')[:5]
    operations_comments = OperationsRecord.objects.all().order_by('-comments')[:5]
    finance_comments = Finance.objects.all().order_by('-comments')[:5]
    sales_comments = SalesRecord.objects.all().order_by('-comments')[:5]

    # Calculate average sales
    days = SalesRecord.objects.all().order_by('-date_of_sale').count() or 1
    average_sales = total_sales/days







    # Bank Graph Data
    bank_totals = SalesRecord.objects.aggregate(
        total_keystone=Sum('keystone'),
        total_zenith=Sum('zenith'),
        total_moniepoint=Sum('moniepoint'),
    )
    bank_graph_data = {
        "banks": ['Keystone', 'Zenith', 'Moniepoint'],
        "amounts": [
            bank_totals['total_keystone'] or 0,
            bank_totals['total_zenith'] or 0,
            bank_totals['total_moniepoint'] or 0
        ]
    }

    # Additional Totals

    total_keystone = bank_totals['total_keystone'] or 0
    total_zenith = bank_totals['total_zenith'] or 0
    total_moniepoint = bank_totals['total_moniepoint'] or 0
    total_bags_returned = SalesRecord.objects.aggregate(Sum('bags_returned'))['bags_returned__sum'] or 0
    total_bags_received = SalesRecord.objects.aggregate(Sum('bags_received_from_production'))['bags_received_from_production__sum'] or 0

    # Context
    context = {
        'total_staff': total_staff,
        'total_sales': total_sales,
        'total_bags_produced': total_bags_produced,
        'staff_info': staff_info,
        'operations_records': operations_records,
        'sales_records': sales_records,
        'total_keystone': total_keystone,
        'total_zenith': total_zenith,
        'total_moniepoint': total_moniepoint,
        'total_bags_returned': total_bags_returned,
        'total_bags_received': total_bags_received,
        'total_expenses': total_expenses,
        'grand_total': grand_total,
        'net':net,
        'finance_records':finance_records,
        'finance_comments':finance_comments,
        'sales_comments':sales_comments,
        'operations_comments':operations_comments,
        'average_sales':average_sales,


    }

    return render(request, 'accounts/supervisor_dashboard.html', context)


@login_required()
def staff_info(request, name):
    info = get_object_or_404(CustomUser, name=name)
    return render(request, 'accounts/staff_info.html', {'info': info})


@login_required
def query_records(request):
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    total_sales = 0
    total_expenses = 0
    total_production = 0

    if start_date and end_date:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Calculate total sum over the selected period
        total_sales = SalesRecord.objects.filter(date_of_sale__range=[start_date, end_date]).aggregate(Sum('total'))['total__sum'] or 0
        total_expenses = Finance.objects.filter(date_of_expense__range=[start_date, end_date]).aggregate(Sum('amount'))['amount__sum'] or 0
        total_production = OperationsRecord.objects.filter(date_produced__range=[start_date, end_date]).aggregate(Sum('bags_produced'))['bags_produced__sum'] or 0
    else:
        start_date = end_date = None  # Avoid rendering "None to None" issue

    context = {
        'total_sales': total_sales,
        'total_expenses': total_expenses,
        'total_production': total_production,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'accounts/query_records.html', context)


@login_required
def receipt_list(request):
    receipts = Finance.objects.exclude(receipt='')  # Fetch only records with receipts
    return render(request, 'accounts/receipts.html', {'receipts': receipts})