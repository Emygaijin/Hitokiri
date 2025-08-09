from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm, BagsForm, ExpenseForm, SalesForm, SpecialSaleForm
from django.db.models.functions import TruncDate
from django.db.models.functions import TruncDay
from .models import OperationsRecord, CustomUser, SalesRecord, Finance,SpecialSale
from django.db.models import Sum, Count, Q, F
from datetime import datetime, timedelta
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.contrib.sessions.models import Session
from django.utils.timezone import now
from decimal import Decimal
from django.contrib import messages


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
                if user.role == 'Production Supervisor':  # Use value from ROLE_CHOICES
                    return redirect('operations_dashboard')
                elif user.role == 'Sales Manager':  # Use value from ROLE_CHOICES
                    return redirect('sales_dashboard')
                elif user.role == 'Supervisor':
                    return redirect('supervisor_dashboard')
                elif user.role == 'Boss':
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
    if request.user.role != 'Production Supervisor':
        return redirect('landing_page')  # Restrict access for non-operations managers
    records = OperationsRecord.objects.all().order_by('-date_produced')
    return render(request, 'accounts/operations_dashboard.html', {'records': records})


# Add bags record view
@login_required
def add_bags_record(request):
    if request.user.role != 'Production Supervisor':
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
    if request.user.role != 'Finance':
        return redirect('landing_page')  # Restrict access for non-operations managers
    else:
        # Total staff
        total_staff = CustomUser.objects.count()

        # Staff information
        staff_info = CustomUser.objects.all()

        # Total sales
        total_sales = SalesRecord.objects.aggregate(total_bags_sold=Sum('bags_sold'))['total_bags_sold'] or 0
        grand_total = SalesRecord.objects.aggregate(total_cash=Sum('total'))['total_cash'] or 0

        # Total production (e.g., bags produced)
        total_bags_produced = OperationsRecord.objects.aggregate(total_bags=Sum('bags_produced'))['total_bags'] or 0

        total_umuahia = SalesRecord.objects.aggregate(total_to_umuahia=Sum('to_umuahia'))['total_to_umuahia'] or 0
        total_law_enforcement = SalesRecord.objects.aggregate(total_law_enforcement=Sum('law_enforcement'))[
                                    'total_law_enforcement'] or 0
        total_rebagged = SalesRecord.objects.aggregate(total_rebagged=Sum('rebagged'))['total_rebagged'] or 0
        total_lost_to_rebagging = SalesRecord.objects.aggregate(total_lost_to_rebagging=Sum('lost_to_rebagging'))[
                                      'total_lost_to_rebagging'] or 0
        total_damaged = SalesRecord.objects.aggregate(total_damaged=Sum('damaged'))['total_damaged'] or 0

        # Available stock
        available_stock = total_bags_produced - total_sales - total_umuahia - total_law_enforcement - total_rebagged - total_lost_to_rebagging - total_damaged

        operations_records = OperationsRecord.objects.all().order_by('-date_produced')[:5]
        sales_records = SalesRecord.objects.all().order_by('-date_of_sale')[:5].annotate(
            expected_total=F('bags_sold') * 400)
        special_sale = SpecialSale.objects.all().order_by('-date_of_sale')[:5]

        finance_records = Finance.objects.all().order_by('-date_of_expense')[:5]

        # Special Sales total qty
        special_sales_total = SpecialSale.objects.aggregate(total=Sum('bags_sold'))['total'] or 0

        # Special sales total..amount
        special_sales = SpecialSale.objects.aggregate(total=Sum('total'))['total'] or 0

        total_bags_sold = total_sales + special_sales_total

        # Combined grand total
        overall_total = grand_total + special_sales

        # Total expenses
        total_expenses = Finance.objects.aggregate(all_expenses=Sum('amount'))['all_expenses'] or 0

        # Calculate net
        net = overall_total - total_expenses
        # Total Diesel from Finance (cost-based)
        total_diesel_expense = Finance.objects.filter(expense_type='Diesel').aggregate(total=Sum('amount'))[
                                   'total'] or 0

        total_fuel_expense = Finance.objects.filter(expense_type='Fuel').aggregate(total=Sum('amount'))['total'] or 0

        # Diesel quantities from OperationsRecord (usage-based)
        diesel_received_qty = OperationsRecord.objects.aggregate(total=Sum('diesel_received'))['total'] or 0
        diesel_used_qty = OperationsRecord.objects.aggregate(total=Sum('diesel_used'))['total'] or 0

        # Set lower diesel limit
        lower_diesel_limit = 100

        # Total stereo
        total_stereo = OperationsRecord.objects.aggregate(all_stereo=Sum('stereo_received'))['all_stereo'] or 0
        total_bad_stereo = OperationsRecord.objects.aggregate(bad=Sum('bad_stereo'))['bad'] or 0
        total_used_stereo = OperationsRecord.objects.aggregate(used=Sum('stereo_used'))['used'] or 0

        total_cone = OperationsRecord.objects.aggregate(total_cone=Sum('cone'))['total_cone'] or 0

        available_stereo = total_stereo - total_bad_stereo - total_used_stereo - total_cone

        # Packaging bags
        total_packaging_bags = OperationsRecord.objects.aggregate(received=Sum('packaging_bags'))['received'] or 0
        total_packaging_bags_used = OperationsRecord.objects.aggregate(used=Sum('packaging_bags_used'))['used'] or 0

        available_packaging_bags = total_packaging_bags - total_packaging_bags_used

        lower_stereo_limit = 80.0

        lower_packaging_bags_limit = 3000

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

        # Discrepancy check (Daily Calculation)
        latest_sale_date = SalesRecord.objects.order_by('-date_of_sale').values_list('date_of_sale', flat=True).first()
        latest_bags_sold = 0
        latest_total = 0
        expected = 0
        discrepancy_alert = None

        if latest_sale_date:
            latest_bags_sold = SalesRecord.objects.filter(date_of_sale=latest_sale_date).aggregate(Sum('bags_sold'))[
                                   'bags_sold__sum'] or 0
            latest_total = SalesRecord.objects.filter(date_of_sale=latest_sale_date).aggregate(Sum('total'))[
                               'total__sum'] or 0
            expected = latest_bags_sold * 400

            if expected != latest_total:
                discrepancy_alert = f"Discrepancy detected for {latest_sale_date}: Expected {expected}, but got {latest_total}. Please review."



    return render(request, 'accounts/finance.html', {
        'operations_records': operations_records,
        'total_sales':total_sales,
        'total_staff':total_staff,
        'available_stock':available_stock,
        'total_bags_produced':total_bags_produced,
        'sales_records': sales_records,
        'special_sale':special_sale,
        'total_bags_sold':total_bags_sold,
        'finance_records': finance_records,
        'expected':expected,
        'staff_info':staff_info,
        'diesel_received_qty':diesel_received_qty,
        'diesel_used_qty':diesel_used_qty,
        'net':net,
        'total_expenses':total_expenses,
        'overall_total':overall_total,
        'total_diesel_expense':total_diesel_expense,
        'total_fuel_expense':total_fuel_expense,
        'start_date': start_date,  # Pass as string
        'end_date': end_date, # Pass as string
        'available_stereo':available_stereo,
        'available_packaging_bags':available_packaging_bags,
        'lower_diesel_limit':lower_diesel_limit,
        'lower_stereo_limit':lower_stereo_limit,
        'lower_packaging_bags_limit':lower_packaging_bags_limit,
    })



# Sales manager dashboard
@login_required
def sales_dashboard(request):
    sales_records = SalesRecord.objects.all().order_by('-date_of_sale')[:25]
    if request.user.role != 'Sales Manager':
        return redirect('landing_page')  # Restrict access for non-Sales
    return render(request, 'accounts/sales_dashboard.html', {'sales_records': sales_records})


# Add sales record view
@login_required()
def add_sales_record(request):
    if request.user.role != 'Sales Manager':
        return redirect('dashboard')  # Restrict access for non-Sales
    if request.method == 'POST':
        form = SalesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales_dashboard')
    else:
        form = SalesForm()
    return render(request, 'accounts/add_sales_records.html', {'form': form})


@login_required()
def add_special_sales_record(request):
    if request.user.role != 'Sales Manager':
        return redirect('dashboard')  # Restrict access for non-Sales
    if request.method == 'POST':
        form = SalesForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('sales_dashboard')
    else:
        form = SpecialSaleForm()
    return render(request, 'accounts/add_special_sales_records.html', {'form': form})


@login_required
def supervisor_dashboard(request):
    if request.user.role not in ['Boss', 'Supervisor']:
        return redirect('landing_page')

    else:
        # Total staff
        total_staff = CustomUser.objects.count()
        finance_records = Finance.objects.all().order_by('-date_of_expense')[:5]

        # Total sales
        total_sales = SalesRecord.objects.aggregate(total_bags_sold=Sum('bags_sold'))['total_bags_sold'] or 0
        grand_total = SalesRecord.objects.aggregate(total_cash=Sum('total'))['total_cash'] or 0


        total_umuahia = SalesRecord.objects.aggregate(total_to_umuahia=Sum('to_umuahia'))['total_to_umuahia'] or 0
        total_law_enforcement = SalesRecord.objects.aggregate(total_law_enforcement=Sum('law_enforcement'))['total_law_enforcement'] or 0
        total_rebagged = SalesRecord.objects.aggregate(total_rebagged=Sum('rebagged'))['total_rebagged'] or 0
        total_lost_to_rebagging = SalesRecord.objects.aggregate(total_lost_to_rebagging=Sum('lost_to_rebagging'))['total_lost_to_rebagging'] or 0
        total_damaged = SalesRecord.objects.aggregate(total_damaged=Sum('damaged'))['total_damaged'] or 0

        # Total production (e.g., bags produced)
        total_bags_produced = OperationsRecord.objects.aggregate(total_bags=Sum('bags_produced'))['total_bags'] or 0

        # Total expenses
        total_expenses = Finance.objects.aggregate(all_expenses=Sum('amount'))['all_expenses'] or 0

        #Available stock
        available_stock = total_bags_produced - total_sales - total_umuahia - total_law_enforcement - total_rebagged - total_lost_to_rebagging - total_damaged


        # Total Diesel from Finance (cost-based)
        total_diesel_expense = Finance.objects.filter(expense_type='Diesel').aggregate(total=Sum('amount'))['total'] or 0
        total_fuel_expense = Finance.objects.filter(expense_type='Fuel').aggregate(total=Sum('amount'))['total'] or 0

        # Special Sales total qty
        special_sales_total = SpecialSale.objects.aggregate(total=Sum('bags_sold'))['total'] or 0

        #Special sales total..amount
        special_sales = SpecialSale.objects.aggregate(total=Sum('total'))['total'] or 0









        #overall bags sold
        total_bags_sold = total_sales + special_sales_total

        total_isuikwuato = special_sales_total+total_sales


        # Combined grand total
        overall_total = grand_total + special_sales

        #Isuikwuato total cash
        cash_isuikwuato = grand_total + special_sales_total

        # Diesel quantities from OperationsRecord (usage-based)
        diesel_received_qty = OperationsRecord.objects.aggregate(total=Sum('diesel_received'))['total'] or 0
        diesel_used_qty = OperationsRecord.objects.aggregate(total=Sum('diesel_used'))['total'] or 0

        #Calculate diesel balance
        available_diesel = diesel_received_qty - diesel_used_qty

        # Set lower diesel limit
        lower_diesel_limit = 100

        # Total stereo
        total_stereo = OperationsRecord.objects.aggregate(all_stereo=Sum('stereo_received'))['all_stereo'] or 0
        total_bad_stereo = OperationsRecord.objects.aggregate(bad=Sum('bad_stereo'))['bad'] or 0
        total_used_stereo = OperationsRecord.objects.aggregate(used=Sum('stereo_used'))['used'] or 0

        total_cone = OperationsRecord.objects.aggregate(total_cone=Sum('cone'))['total_cone'] or 0

        available_stereo = total_stereo - total_bad_stereo - total_used_stereo - total_cone

        # Packaging bags
        total_packaging_bags = OperationsRecord.objects.aggregate(received=Sum('packaging_bags'))['received'] or 0
        total_packaging_bags_used = OperationsRecord.objects.aggregate(used=Sum('packaging_bags_used'))['used'] or 0

        available_packaging_bags = total_packaging_bags - total_packaging_bags_used

        lower_stereo_limit = 80.0

        lower_packaging_bags_limit = 3000


        # Calculate net
        net = overall_total - total_expenses

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
        sales_records = SalesRecord.objects.all().order_by('-date_of_sale')[:5].annotate(expected_total=F('bags_sold') * 400)
        operations_comments = OperationsRecord.objects.all().order_by('-comments')[:5]
        finance_comments = Finance.objects.all().order_by('-comments')[:5]
        sales_comments = SalesRecord.objects.all().order_by('-comments')[:5]
        special_sale = SpecialSale.objects.all().order_by('-date_of_sale')[:5]

        # Calculate average sales
        # days = SalesRecord.objects.all().order_by('-date_of_sale').count() or 1
        # average_sales = total_sales / days

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

        # Discrepancy check (Daily Calculation)
        latest_sale_date = SalesRecord.objects.order_by('-date_of_sale').values_list('date_of_sale', flat=True).first()
        latest_bags_sold = 0
        latest_total = 0
        expected = 0
        discrepancy_alert = None

        if latest_sale_date:
            latest_bags_sold = SalesRecord.objects.filter(date_of_sale=latest_sale_date).aggregate(Sum('bags_sold'))['bags_sold__sum'] or 0
            latest_total = SalesRecord.objects.filter(date_of_sale=latest_sale_date).aggregate(Sum('total'))['total__sum'] or 0
            expected = latest_bags_sold * 400

            if expected != latest_total:
                discrepancy_alert = f"Discrepancy detected for {latest_sale_date}: Expected {expected}, but got {latest_total}. Please review."

        # Additional Totals
        total_keystone = bank_totals['total_keystone'] or 0
        total_zenith = bank_totals['total_zenith'] or 0
        total_moniepoint = bank_totals['total_moniepoint'] or 0

        latest_bags = SalesRecord.objects.filter(date_of_sale=latest_sale_date).aggregate(Sum('bags_sold'))[
                               'bags_sold__sum'] or 0
        expected_total = latest_bags * 400


        # Context
        context = {
            'total_staff': total_staff,
            'total_sales': total_sales,
            'total_bags_produced': total_bags_produced,
            'staff_info': staff_info,
            'operations_records': operations_records,
            'special_sales_total': special_sales_total,
            'overall_total': overall_total,
            'sales_records': sales_records,
            'total_keystone': total_keystone,
            'expected_total':expected_total,
            'total_zenith': total_zenith,
            'total_moniepoint': total_moniepoint,
            'total_expenses': total_expenses,
            'grand_total': grand_total,
            'total_bags_sold':total_bags_sold,
            'total_diesel_expense': total_diesel_expense,
            'total_fuel_expense': total_fuel_expense,
            'diesel_received_qty': diesel_received_qty,
            'diesel_used_qty': diesel_used_qty,
            'net': net,
            'available_stock': available_stock,
            'lower_stereo_limit':lower_stereo_limit,
            'lower_packaging_bags_limit':lower_packaging_bags_limit,
            'total_stereo':total_stereo,
            'cash_isuikwuato':cash_isuikwuato,
            'total_bad_stereo':total_bad_stereo,
            'total_used_stereo':total_used_stereo,
            'available_stereo':available_stereo,
            'total_packaging_bags':total_packaging_bags,
            'total_packaging_bags_used':total_packaging_bags_used,
            'available_packaging_bags':available_packaging_bags,
            'finance_records': finance_records,
            'finance_comments': finance_comments,
            'sales_comments': sales_comments,
            'operations_comments': operations_comments,
            'expected': expected,
            'total_cone': total_cone,
            'latest_bags_sold': latest_bags_sold,
            'latest_total': latest_total,
            'available_diesel':available_diesel,
            'discrepancy_alert': discrepancy_alert,
            'lower_diesel_limit': lower_diesel_limit,
            'special_sale':special_sale,
            'total_isuikwuato':total_isuikwuato,
        }

    return render(request, 'accounts/supervisor_dashboard.html', context)



@login_required()
def staff_info(request, name):
    if request.user.role not in ['Boss', 'Supervisor', 'Finance']:
        return redirect('landing_page')
    else:
        info = get_object_or_404(CustomUser, name=name)
    return render(request, 'accounts/staff_info.html', {'info': info})


@login_required
def query_records(request):
    if request.user.role not in ['Boss', 'Finance', 'Supervisor']:
        return redirect('landing_page')
    else:
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')

        total_sales = 0
        total_expenses = 0
        total_production = 0
        total_stereo_used = 0
        total_packaging_bags_used = 0
        total_diesel_received = 0
        total_diesel_used = 0
        total_fuel_used = 0
        production_cost_per_bag = 0
        total_production_cost = 0

        if start_date and end_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

            total_sales = SalesRecord.objects.filter(date_of_sale__range=[start_date, end_date]).aggregate(Sum('total'))['total__sum'] or 0
            total_expenses = Finance.objects.filter(date_of_expense__range=[start_date, end_date]).aggregate(Sum('amount'))['amount__sum'] or 0
            total_production = OperationsRecord.objects.filter(date_produced__range=[start_date, end_date]).aggregate(Sum('bags_produced'))['bags_produced__sum'] or 0

            operations_qs = OperationsRecord.objects.filter(date_produced__range=[start_date, end_date])
            total_stereo_used = operations_qs.aggregate(Sum('stereo_used'))['stereo_used__sum'] or 0
            total_packaging_bags_used = operations_qs.aggregate(Sum('packaging_bags_used'))['packaging_bags_used__sum'] or 0
            total_diesel_received = operations_qs.aggregate(Sum('diesel_received'))['diesel_received__sum'] or 0
            total_diesel_used = operations_qs.aggregate(Sum('diesel_used'))['diesel_used__sum'] or 0

            total_fuel_used = Finance.objects.filter(
                date_of_expense__range=[start_date, end_date],
                expense_type='Fuel'
            ).aggregate(Sum('amount'))['amount__sum'] or 0

            # ➕ Cost calculation
            cost_of_stereo = total_stereo_used * 3200
            cost_of_bags = total_packaging_bags_used * Decimal('15.5')
            cost_of_diesel = total_diesel_used * 1200
            total_production_cost = cost_of_stereo + cost_of_bags + cost_of_diesel

            # ➗ Production cost per bag
            if total_production > 0:
                production_cost_per_bag = total_production_cost / total_production

        context = {
            'total_sales': total_sales,
            'total_expenses': total_expenses,
            'total_production': total_production,
            'total_stereo_used': total_stereo_used,
            'total_packaging_bags_used': total_packaging_bags_used,
            'total_diesel_received': total_diesel_received,
            'total_diesel_used': total_diesel_used,
            'total_fuel_used': total_fuel_used,
            'production_cost_per_bag': round(production_cost_per_bag, 2),
            'total_production_cost': round(total_production_cost, 2),
            'start_date': start_date,
            'end_date': end_date,
        }
    return render(request, 'accounts/query_records.html', context)



@login_required
def receipt_list(request):
    receipts = Finance.objects.exclude(receipt='')  # Fetch only records with receipts
    return render(request, 'accounts/receipts.html', {'receipts': receipts})


@login_required
def query_expenses(request):
    if request.user.role not in ['Boss', 'Finance','Supervisor']:
        return redirect('landing_page')

    else:
        start_date = request.GET.get('start_date', '')
        end_date = request.GET.get('end_date', '')
        selected_expense = request.GET.get('expense_type', '')

        start_date_obj = end_date_obj = None
        expense_summary = []
        expense_details = []
        total_sum = 0

        if start_date and end_date:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

            qs = Finance.objects.filter(date_of_expense__range=[start_date_obj, end_date_obj])

            # Summary
            expense_summary = (
                qs.values('expense_type')
                .annotate(total_amount=Sum('amount'))
                .order_by('-total_amount')
            )

            total_sum = qs.aggregate(total=Sum('amount'))['total'] or 0

            # Drill-down if expense_type is selected
            if selected_expense:
                expense_details = qs.filter(expense_type=selected_expense).order_by('-date_of_expense')

        context = {
            'expense_summary': expense_summary,
            'expense_details': expense_details,
            'total_sum': total_sum,
            'start_date': start_date,
            'end_date': end_date,
            'selected_expense': selected_expense,
        }
    return render(request, 'accounts/query_expenses.html', context)



# Edit records by only supervisor
@login_required
def edit_sales_record(request, pk):
    if request.user.role !='Supervisor':
        messages.error(request, "You don't have permission to edit records.")
        return redirect('landing_page')


    record = get_object_or_404(SalesRecord, pk=pk)

    if request.method == 'POST':
        form = SalesForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Sales record updated successfully.")
            return redirect('supervisor_dashboard')
    else:
        form = SalesForm(instance=record)

    return render(request, 'accounts/edit_sales_record.html', {'form': form})




# Edit Operations Record
@login_required
def edit_operations_record(request, pk):
    if request.user.role !='Supervisor':
        messages.error(request, "You don't have permission to edit records.")
        return redirect('landing_page')

    record = get_object_or_404(OperationsRecord, pk=pk)

    if request.method == 'POST':
        form = BagsForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Operations record updated successfully.")
            return redirect('supervisor_dashboard')
    else:
        form = BagsForm(instance=record)

    return render(request, 'accounts/edit_operations_record.html', {'form': form})




# Edit Finance Record
@login_required
def edit_finance_record(request, pk):
    if request.user.role !='Supervisor':
        messages.error(request, "You don't have permission to edit records.")
        return redirect('landing_page')

    record = get_object_or_404(Finance, pk=pk)

    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, "Finance record updated successfully.")
            return redirect('supervisor_dashboard')
    else:
        form = ExpenseForm(instance=record)

    return render(request, 'accounts/edit_finance_record.html', {'form': form})
