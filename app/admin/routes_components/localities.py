from flask import render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.extensions import db
from app.models.agenda import Locality
from app.utils.logging_helper import log_activity
from .. import admin_bp

@admin_bp.route('/localities', methods=['GET', 'POST'])
@login_required
def localities():
    if request.method == 'POST':
        name = request.form.get('name')
        if not name:
            flash('El nombre es requerido', 'error')
        else:
            locality = Locality(name=name)
            db.session.add(locality)
            db.session.commit()
            log_activity("LOCALITY_CREATE", f"Localidad creada: {name}")
            flash(f'Localidad {name} creada correctamente', 'success')
        return redirect(url_for('admin.localities'))
        
    all_localities = Locality.query.order_by(Locality.name).all()
    return render_template('admin/localities.html', localities=all_localities)

@admin_bp.route('/localities/<int:id>/delete', methods=['POST'])
@login_required
def delete_locality(id):
    locality = Locality.query.get_or_404(id)
    name = locality.name
    
    # Check if used
    if locality.slots.count() > 0 or locality.reservations.count() > 0:
        flash('No se puede eliminar una localidad que tiene turnos asignados', 'error')
    else:
        db.session.delete(locality)
        db.session.commit()
        log_activity("LOCALITY_DELETE", f"Localidad eliminada: {name}")
        flash(f'Localidad {name} eliminada', 'success')
        
    return redirect(url_for('admin.localities'))
