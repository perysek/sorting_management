from flask import Blueprint, render_template, request
from app import db
from app.models import DaneRaportu

bp = Blueprint('main', __name__)


@bp.route('/')
def index():
    """Dashboard view with report table."""
    sort_by = request.args.get('sort', 'data_selekcji')
    order = request.args.get('order', 'desc')
    
    # Filters
    filters = {
        'data_selekcji': request.args.get('filter_data', ''),
        'operator': request.args.get('filter_operator', ''),
        'nr_raportu': request.args.get('filter_nr_raportu', ''),
        'nr_niezgodnosci': request.args.get('filter_nr_niezgodnosci', ''),
        'nr_instrukcji': request.args.get('filter_nr_instrukcji', ''),
    }
    
    # Build query
    query = DaneRaportu.query
    
    # Apply filters
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
    
    reports = query.all()
    
    return render_template(
        'dashboard/index.html',
        reports=reports,
        sort_by=sort_by,
        order=order,
        filters=filters
    )
