from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from app import db
from app.models import DaneRaportu, BrakiDefektyRaportu, Operator

bp = Blueprint('reports', __name__)


@bp.route('/<int:report_id>')
def view(report_id):
    """View single report details."""
    report = DaneRaportu.query.get_or_404(report_id)
    return render_template('reports/view.html', report=report)


@bp.route('/create', methods=['GET', 'POST'])
def create():
    """Create new report form."""
    if request.method == 'POST':
        try:
            # Get next report number
            max_report = db.session.query(DaneRaportu).order_by(DaneRaportu.id.desc()).first()
            if max_report and max_report.nr_raportu and max_report.nr_raportu.isdigit():
                next_nr = int(max_report.nr_raportu) + 1
            elif max_report:
                next_nr = max_report.id + 1
            else:
                next_nr = 1

            # Parse date
            data_selekcji = None
            if request.form.get('data_selekcji'):
                data_selekcji = datetime.strptime(request.form['data_selekcji'], '%Y-%m-%d').date()

            # Create report
            report = DaneRaportu(
                nr_raportu=str(next_nr),
                operator_id=int(request.form['operator_id']) if request.form.get('operator_id') else None,
                nr_niezgodnosci=request.form.get('nr_niezgodnosci', ''),
                nr_instrukcji=request.form.get('nr_instrukcji', ''),
                selekcja_na_biezaco=request.form.get('selekcja_na_biezaco') == 'on',
                ilosc_detali_sprawdzonych=int(request.form.get('ilosc_detali_sprawdzonych', 0)),
                zalecana_wydajnosc=float(request.form['zalecana_wydajnosc']) if request.form.get('zalecana_wydajnosc') else None,
                czas_pracy=float(request.form.get('czas_pracy', 0)),
                uwagi=request.form.get('uwagi', ''),
                uwagi_do_wydajnosci=request.form.get('uwagi_do_wydajnosci', ''),
                data_selekcji=data_selekcji
            )
            db.session.add(report)
            db.session.flush()

            # Add defects
            defekt_names = request.form.getlist('defekt_nazwa[]')
            defekt_ilosci = request.form.getlist('defekt_ilosc[]')
            
            for name, ilosc in zip(defekt_names, defekt_ilosci):
                if name and ilosc:
                    defekt = BrakiDefektyRaportu(
                        raport_id=report.id,
                        defekt=name,
                        ilosc=int(ilosc)
                    )
                    db.session.add(defekt)

            db.session.commit()
            flash(f'Raport #{next_nr} został pomyślnie zapisany!', 'success')
            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Błąd zapisu do bazy danych: {str(e)}', 'error')

    operators = Operator.query.all()
    return render_template('reports/create.html', operators=operators)


@bp.route('/<int:report_id>/edit', methods=['GET', 'POST'])
def edit(report_id):
    """Edit existing report."""
    report = DaneRaportu.query.get_or_404(report_id)
    
    if request.method == 'POST':
        try:
            # Update report fields
            if request.form.get('data_selekcji'):
                report.data_selekcji = datetime.strptime(request.form['data_selekcji'], '%Y-%m-%d').date()
            
            report.operator_id = int(request.form['operator_id']) if request.form.get('operator_id') else None
            report.nr_niezgodnosci = request.form.get('nr_niezgodnosci', '')
            report.nr_instrukcji = request.form.get('nr_instrukcji', '')
            report.selekcja_na_biezaco = request.form.get('selekcja_na_biezaco') == 'on'
            report.ilosc_detali_sprawdzonych = int(request.form.get('ilosc_detali_sprawdzonych', 0))
            report.zalecana_wydajnosc = float(request.form['zalecana_wydajnosc']) if request.form.get('zalecana_wydajnosc') else None
            report.czas_pracy = float(request.form.get('czas_pracy', 0))
            report.uwagi = request.form.get('uwagi', '')
            report.uwagi_do_wydajnosci = request.form.get('uwagi_do_wydajnosci', '')

            # Update defects - remove old ones and add new
            BrakiDefektyRaportu.query.filter_by(raport_id=report.id).delete()
            
            defekt_names = request.form.getlist('defekt_nazwa[]')
            defekt_ilosci = request.form.getlist('defekt_ilosc[]')
            
            for name, ilosc in zip(defekt_names, defekt_ilosci):
                if name and ilosc:
                    defekt = BrakiDefektyRaportu(
                        raport_id=report.id,
                        defekt=name,
                        ilosc=int(ilosc)
                    )
                    db.session.add(defekt)

            db.session.commit()
            flash(f'Raport #{report.nr_raportu} został zaktualizowany!', 'success')
            return redirect(url_for('main.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Błąd zapisu: {str(e)}', 'error')

    operators = Operator.query.all()
    return render_template('reports/edit.html', report=report, operators=operators)


@bp.route('/<int:report_id>/delete', methods=['POST'])
def delete(report_id):
    """Delete a report."""
    report = DaneRaportu.query.get_or_404(report_id)
    try:
        db.session.delete(report)
        db.session.commit()
        flash(f'Raport #{report.nr_raportu} został usunięty.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Błąd usuwania: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))
