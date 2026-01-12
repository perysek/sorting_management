from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Operator, KategoriaZrodlaDanych

bp = Blueprint('operators', __name__)


@bp.route('/')
def index():
    """List all operators and show add form."""
    operators = Operator.query.all()
    categories = KategoriaZrodlaDanych.query.all()
    return render_template('operators/index.html', operators=operators, categories=categories)


@bp.route('/add', methods=['POST'])
def add():
    """Add new operator."""
    try:
        nr_operatora = request.form.get('nr_operatora')
        imie_nazwisko = request.form.get('imie_nazwisko')
        dzial_id = request.form.get('dzial_id')

        if not all([nr_operatora, imie_nazwisko, dzial_id]):
            flash('Numer, Imię i Nazwisko oraz Dział są wymagane.', 'error')
            return redirect(url_for('operators.index'))

        operator = Operator(
            nr_operatora=int(nr_operatora),
            imie_nazwisko=imie_nazwisko,
            dzial_id=int(dzial_id)
        )
        db.session.add(operator)
        db.session.commit()
        flash('Operator dodany pomyślnie!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Błąd: {str(e)}', 'error')

    return redirect(url_for('operators.index'))


@bp.route('/<int:operator_id>/delete', methods=['POST'])
def delete(operator_id):
    """Delete an operator."""
    operator = Operator.query.get_or_404(operator_id)
    try:
        db.session.delete(operator)
        db.session.commit()
        flash(f'Operator {operator.imie_nazwisko} został usunięty.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Błąd usuwania: {str(e)}', 'error')
    
    return redirect(url_for('operators.index'))
