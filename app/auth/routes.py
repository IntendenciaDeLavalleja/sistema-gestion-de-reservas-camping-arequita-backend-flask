from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models.user import AdminUser, TwoFactorCode
from app.services.email_service import send_2fa_email
from app.extensions import db, limiter
from app.utils.logging_helper import log_activity
import secrets
import random
from datetime import datetime
from . import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def login():
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('admin.dashboard'))
        
        # Generate simple arithmetic captcha
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        session['captcha_result'] = num1 + num2
        captcha_question = f"¿Cuánto es {num1} + {num2}?"
        
        return render_template('admin/login.html', captcha_question=captcha_question)

    # Handle POST (Strictly Form Data for Web)
    username = request.form.get('username')
    password = request.form.get('password')
    captcha_answer = request.form.get('captcha')
    
    # Verify Captcha
    stored_captcha = session.get('captcha_result')
    if captcha_answer is None or str(captcha_answer) != str(stored_captcha):
        session.pop('captcha_result', None)
        log_activity("WEB_LOGIN_CAPTCHA_FAIL", f"Captcha fallido para usuario: {username}")
        flash('Captcha incorrecto. Intenta de nuevo.', 'error')
        return redirect(url_for('auth.login'))

    # Clear captcha after validation
    session.pop('captcha_result', None)

    user = AdminUser.query.filter_by(username=username).first()
    if user and user.check_password(password):
        # Valid credentials, start 2FA
        session['2fa_user_id'] = user.id
        
        # Generate 6-digit code
        code = ''.join([secrets.choice('0123456789') for _ in range(6)])
        
        # Save code in DB
        tf_code = TwoFactorCode(user_id=user.id, code=code)
        db.session.add(tf_code)
        db.session.commit()
        
        # Send mail
        send_2fa_email(user.email, code)
        
        log_activity("WEB_LOGIN_STEP1_SUCCESS", f"Credenciales válidas. Código 2FA enviado a {user.email}", user)
        return redirect(url_for('auth.verify_2fa'))
    
    log_activity("WEB_LOGIN_FAIL", f"Intento de login fallido: {username}")
    flash('Usuario o contraseña incorrectos', 'error')
    return render_template('admin/login.html')

@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def verify_2fa():
    if '2fa_user_id' not in session:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        code = request.form.get('code')
        user_id = session.get('2fa_user_id')
        user = AdminUser.query.get(user_id)
        
        if not user:
            session.pop('2fa_user_id', None)
            return redirect(url_for('auth.login'))
            
        # Find the latest unconsumed code
        tf_code = TwoFactorCode.query.filter_by(user_id=user.id, consumed_at=None)\
            .order_by(TwoFactorCode.created_at.desc()).first()
            
        if tf_code and tf_code.verify_code(code):
            tf_code.consumed_at = datetime.utcnow()
            db.session.commit()
            
            login_user(user)
            session.pop('2fa_user_id', None)
            log_activity("LOGIN_2FA_SUCCESS", "Verificación 2FA correcta. Sesión iniciada.", user)
            return redirect(url_for('admin.dashboard'))
        else:
            log_activity("LOGIN_2FA_FAIL", f"Código 2FA incorrecto para usuario ID: {user_id}", user)
            flash('Código inválido o expirado', 'error')
            
    return render_template('admin/2fa.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_activity("LOGOUT", "Usuario cerró sesión.")
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/status')
def status():
    if current_user.is_authenticated:
        return jsonify({"status": "authenticated", "user": current_user.username})
    return jsonify({"status": "anonymous"})
