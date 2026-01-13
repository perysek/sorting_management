from flask import Blueprint, render_template, request
from sqlalchemy.orm import joinedload
from sqlalchemy import func
from datetime import datetime, timedelta
from app import db
from app.models import DaneRaportu, BrakiDefektyRaportu

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Dashboard view with report table - optimized with pagination and date filters."""
    
    # Pagination params
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Sorting params
    sort_by = request.args.get('sort', 'data_selekcji')
    order = request.args.get('order', 'desc')
    
    # Date range filter with smart defaults
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    preset = request.args.get('preset', 'last_month')  # Default to last month
    
    # Apply preset if no custom dates
    if not date_from and not date_to:
        today = datetime.now().date()
        if preset == 'last_week':
            date_from = today - timedelta(days=7)
        elif preset == 'last_month':
            date_from = today - timedelta(days=30)
        elif preset == 'this_month':
            # First day of current month
            date_from = today.replace(day=1)
        elif preset == 'previous_month':
            # First day of previous month
            first_of_this_month = today.replace(day=1)
            last_of_prev_month = first_of_this_month - timedelta(days=1)
            date_from = last_of_prev_month.replace(day=1)
            date_to = last_of_prev_month
        elif preset == 'last_quarter':
            date_from = today - timedelta(days=90)
        elif preset == 'this_year':
            # First day of current year
            date_from = today.replace(month=1, day=1)
        elif preset == 'previous_year':
            # Previous year (Jan 1 to Dec 31)
            date_from = today.replace(year=today.year - 1, month=1, day=1)
            date_to = today.replace(year=today.year - 1, month=12, day=31)
        elif preset == 'last_year':
            date_from = today - timedelta(days=365)
        # preset == 'all' leaves date_from empty
    else:
        # Parse custom date strings
        if date_from:
            date_from = datetime.strptime(date_from, '%Y-%m-%d').date()
        if date_to:
            date_to = datetime.strptime(date_to, '%Y-%m-%d').date()
    
    # Text filters
    filters = {
        'data_selekcji': date_from if date_from else '',
        'operator': request.args.get('filter_operator', ''),
        'nr_raportu': request.args.get('filter_nr_raportu', ''),
        'nr_niezgodnosci': request.args.get('filter_nr_niezgodnosci', ''),
        'nr_instrukcji': request.args.get('filter_nr_instrukcji', ''),
    }
    
    # Build query with eager loading to avoid N+1
    query = DaneRaportu.query.options(
        joinedload(DaneRaportu.operator),
        joinedload(DaneRaportu.braki_defekty)
    )
    
    # Apply date range filter
    if date_from:
        query = query.filter(DaneRaportu.data_selekcji >= date_from)
    if date_to:
        query = query.filter(DaneRaportu.data_selekcji <= date_to)
    
    # Apply text filters
    if filters['nr_raportu']:
        query = query.filter(DaneRaportu.nr_raportu.ilike(f"%{filters['nr_raportu']}%"))
    if filters['nr_niezgodnosci']:
        query = query.filter(DaneRaportu.nr_niezgodnosci.ilike(f"%{filters['nr_niezgodnosci']}%"))
    if filters['nr_instrukcji']:
        query = query.filter(DaneRaportu.nr_instrukcji.ilike(f"%{filters['nr_instrukcji']}%"))
    
    # Apply sorting
    valid_sort_columns = ['data_selekcji', 'nr_raportu', 'nr_niezgodnosci', 'nr_instrukcji', 
                          'ilosc_detali_sprawdzonych', 'czas_pracy', 'zalecana_wydajnosc']
    if sort_by in valid_sort_columns:
        column = getattr(DaneRaportu, sort_by)
        if order == 'desc':
            query = query.order_by(column.desc())
        else:
            query = query.order_by(column.asc())
    else:
        query = query.order_by(DaneRaportu.data_selekcji.desc())
    
    # Pre-compute stats with SQL for efficiency (on filtered data)
    stats_query = db.session.query(
        func.count(DaneRaportu.id),
        func.coalesce(func.sum(DaneRaportu.ilosc_detali_sprawdzonych), 0),
        func.coalesce(func.sum(DaneRaportu.czas_pracy), 0)
    )
    
    # Apply same date filters to stats
    if date_from:
        stats_query = stats_query.filter(DaneRaportu.data_selekcji >= date_from)
    if date_to:
        stats_query = stats_query.filter(DaneRaportu.data_selekcji <= date_to)
    
    stats_result = stats_query.first()
    
    # Get total defects with SQL (sum from braki_defekty_raportow)
    defects_query = db.session.query(
        func.coalesce(func.sum(BrakiDefektyRaportu.ilosc), 0)
    ).join(DaneRaportu, BrakiDefektyRaportu.raport_id == DaneRaportu.id)
    
    if date_from:
        defects_query = defects_query.filter(DaneRaportu.data_selekcji >= date_from)
    if date_to:
        defects_query = defects_query.filter(DaneRaportu.data_selekcji <= date_to)
    
    total_defects = defects_query.scalar() or 0
    
    # Calculate averages
    avg_scrap_rate = 0
    avg_productivity = 0
    
    if stats_result[0] > 0:  # If there are any reports
        # Average scrap rate = (total defects / total parts checked) * 100
        if stats_result[1] > 0:
            avg_scrap_rate = (total_defects / stats_result[1]) * 100
        
        # Average productivity = total parts checked / total hours worked
        if stats_result[2] > 0:
            avg_productivity = stats_result[1] / stats_result[2]
    
    stats = {
        'count': stats_result[0],
        'parts_checked': stats_result[1],
        'hours_worked': stats_result[2],
        'total_defects': total_defects,
        'average_scrap_rate': avg_scrap_rate,
        'average_productivity': avg_productivity
    }
    
    # Paginate results
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Lazy load missing MOSYS data
    reports_needing_mosys = [r for r in pagination.items 
                             if r.data_niezgodnosci is None and r.nr_niezgodnosci]
    
    if reports_needing_mosys:
        try:
            from MOSYS_data_functions import get_batch_niezgodnosc_details
            nr_list = [r.nr_niezgodnosci for r in reports_needing_mosys]
            mosys_data = get_batch_niezgodnosc_details(nr_list)
            
            for report in reports_needing_mosys:
                if report.nr_niezgodnosci in mosys_data:
                    data = mosys_data[report.nr_niezgodnosci]
                    report.data_niezgodnosci = data.get('data_niezgodnosci')
                    report.nr_zamowienia = data.get('nr_zamowienia')
                    report.kod_detalu = data.get('kod_detalu')
            
            db.session.commit()
        except Exception as e:
            print(f"MOSYS lazy load error: {e}")
            db.session.rollback()
    
    return render_template(
        'dashboard/index.html',
        reports=pagination.items,
        pagination=pagination,
        stats=stats,
        sort_by=sort_by,
        order=order,
        filters=filters,
        preset=preset,
        date_from=date_from.isoformat() if isinstance(date_from, datetime) or hasattr(date_from, 'isoformat') else '',
        date_to=date_to.isoformat() if isinstance(date_to, datetime) or hasattr(date_to, 'isoformat') else ''
    )
