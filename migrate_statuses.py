from app import create_app, db
from app.models.camping import Suggestion, PreReservation

app = create_app()
with app.app_context():
    # Suggestions
    count_new = Suggestion.query.filter_by(status='new').update({'status': 'nuevo'}, synchronize_session=False)
    count_rev = Suggestion.query.filter_by(status='reviewed').update({'status': 'revisado'}, synchronize_session=False)
    count_arc = Suggestion.query.filter_by(status='archived').update({'status': 'archivado'}, synchronize_session=False)
    
    # PreReservations
    p_pend = PreReservation.query.filter_by(status='pending').update({'status': 'pendiente'}, synchronize_session=False)
    p_conf = PreReservation.query.filter_by(status='confirmed').update({'status': 'confirmado'}, synchronize_session=False)
    p_act = PreReservation.query.filter_by(status='active').update({'status': 'activo'}, synchronize_session=False)
    p_comp = PreReservation.query.filter_by(status='completed').update({'status': 'completado'}, synchronize_session=False)
    p_exp = PreReservation.query.filter_by(status='expired').update({'status': 'expirado'}, synchronize_session=False)
    p_arc = PreReservation.query.filter_by(status='archived_admin').update({'status': 'archivado_admin'}, synchronize_session=False)

    db.session.commit()
    print(f"Sugerencias: {count_new} nuevas, {count_rev} revisadas, {count_arc} archivadas")
    print(f"Pre-reservas: {p_pend} pend, {p_conf} conf, {p_act} act, {p_comp} comp, {p_exp} exp, {p_arc} arc")
