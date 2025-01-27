from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, BagsForm, ExpenseForm, SalesForm
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncDay
from .models import OperationsRecord, CustomUser, SalesRecord, Finance
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta


# Landing page (Main page)
def landing_page(request):
    return render(request, 'accounts/landing_page.html')


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



@login_required()
def finance_office(request):
    operations_records = OperationsRecord.objects.all().order_by('-date_produced')[:5]
    sales_records = SalesRecord.objects.all().order_by('-date_of_sale')[:5]
    finance_records = Finance.objects.all()

    return render(request, 'accounts/finance.html', {'operations_records':operations_records, 'sales_records':sales_records,'finance_records':finance_records})



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
    days = SalesRecord.objects.all().order_by('-date_of_sale').count()
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


