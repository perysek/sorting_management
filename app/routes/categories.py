from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import KategoriaZrodlaDanych

bp = Blueprint('categories', __name__)


@bp.route('/')
def index():
    """List all categories and show add form."""
    categories = KategoriaZrodlaDanych.query.all()
    return render_template('categories/index.html', categories=categories)


@bp.route('/add', methods=['POST'])
def add():
    """Add new category."""
    try:
        opis_kategorii = request.form.get('opis_kategorii')
        koszt_pracy = request.form.get('koszt_pracy')

        if not opis_kategorii:
            flash('Opis kategorii jest wymagany.', 'error')
            return redirect(url_for('categories.index'))

        category = KategoriaZrodlaDanych(
            opis_kategorii=opis_kategorii,
            koszt_pracy=float(koszt_pracy) if koszt_pracy else None
        )
        db.session.add(category)
        db.session.commit()
        flash('Kategoria dodana pomyślnie!', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Błąd: {str(e)}', 'error')

    return redirect(url_for('categories.index'))


@bp.route('/<int:category_id>/edit', methods=['GET', 'POST'])
def edit(category_id):
    """Edit a category."""
    category = KategoriaZrodlaDanych.query.get_or_404(category_id)
    
    if request.method == 'POST':
        try:
            opis_kategorii = request.form.get('opis_kategorii')
            koszt_pracy = request.form.get('koszt_pracy')

            if not opis_kategorii:
                flash('Opis kategorii jest wymagany.', 'error')
                return render_template('categories/edit.html', category=category)

            category.opis_kategorii = opis_kategorii
            category.koszt_pracy = float(koszt_pracy) if koszt_pracy else None
            db.session.commit()
            flash('Kategoria zaktualizowana pomyślnie!', 'success')
            return redirect(url_for('categories.index'))

        except Exception as e:
            db.session.rollback()
            flash(f'Błąd: {str(e)}', 'error')
    
    return render_template('categories/edit.html', category=category)


@bp.route('/<int:category_id>/delete', methods=['POST'])
def delete(category_id):
    """Delete a category."""
    category = KategoriaZrodlaDanych.query.get_or_404(category_id)
    try:
        db.session.delete(category)
        db.session.commit()
        flash(f'Kategoria "{category.opis_kategorii}" została usunięta.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Błąd usuwania: {str(e)}', 'error')
    
    return redirect(url_for('categories.index'))
