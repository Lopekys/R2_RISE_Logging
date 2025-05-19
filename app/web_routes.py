from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.config_manager import load_config, save_config
from app.auth_session import auth_session
from app.bot_controller import start_bot, stop_bot, is_bot_running
from pathlib import Path

main = Blueprint('main', __name__)
CREDENTIALS_PATH = Path("credentials.json")


@main.route('/', methods=['GET', 'POST'])
def index():
    config = load_config()

    if request.method == 'POST':
        config['telegram']['api_id'] = request.form['api_id']
        config['telegram']['api_hash'] = request.form['api_hash']
        config['telegram']['phone'] = request.form['phone']
        config['telegram']['bot_username'] = request.form['bot_username']
        config['google_sheets']['sheet_id'] = request.form['sheet_id']

        save_config(config)

        file = request.files.get('credentials_file')
        if file and file.filename:
            file.save(CREDENTIALS_PATH)
            flash('✅ credentials.json загружен', 'success')
        else:
            flash('✅ Настройки сохранены', 'success')

        return redirect(url_for('main.index'))

    return render_template('index.html', config=config, bot_running=is_bot_running())


@main.route('/start')
def start():
    if is_bot_running():
        flash("⚠️ Бот уже запущен", "warning")
        return redirect(url_for('main.index'))

    auth_session.start_auth_flow()

    if auth_session.status == "awaiting_code":
        flash("📱 Введите код из Telegram", "info")
        return redirect(url_for('main.enter_code'))
    elif auth_session.status == "ready":
        start_bot()
        flash("✅ Бот запущен", "success")
        return redirect(url_for('main.index'))

    flash("❌ Не удалось запустить бота", "danger")
    return redirect(url_for('main.index'))


@main.route('/enter_code', methods=['GET'])
def enter_code():
    return render_template('enter_code.html')


@main.route('/submit_code', methods=['POST'])
def submit_code():
    code = request.form['code']
    result = auth_session.sign_in_with_code(code)

    if result == "password_needed":
        return redirect(url_for('main.enter_password'))
    elif result == "success":
        start_bot()
        flash("✅ Авторизация успешна, бот запущен", "success")
        return redirect(url_for('main.index'))
    else:
        flash("❌ Ошибка авторизации", "danger")
        return redirect(url_for('main.enter_code'))


@main.route('/enter_password', methods=['GET'])
def enter_password():
    return render_template('enter_password.html')


@main.route('/submit_password', methods=['POST'])
def submit_password():
    password = request.form['password']
    result = auth_session.submit_2fa_password(password)

    if result == "success":
        start_bot()
        flash("✅ Авторизация завершена, бот запущен", "success")
        return redirect(url_for('main.index'))
    else:
        flash(f"❌ Ошибка авторизации: {result}", "danger")
        return redirect(url_for('main.enter_password'))


@main.route('/stop')
def stop():
    if stop_bot():
        flash("🛑 Бот остановлен", "info")
    else:
        flash("⚠️ Бот не был запущен", "warning")
    return redirect(url_for('main.index'))


@main.route('/logs')
def view_logs():
    log_path = Path("bot_logger.log")
    if log_path.exists():
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-100:]
        log_output = "".join(lines)
    else:
        log_output = "Лог-файл отсутствует."

    if request.args.get("ajax") == "1":
        return jsonify({"logs": log_output})

    config = load_config()
    return render_template("index.html", config=config, bot_running=is_bot_running(), log_output=log_output)


@main.route('/clear_logs')
def clear_logs():
    log_path = Path("bot_logger.log")
    if log_path.exists():
        log_path.write_text("")
        flash("🧹 Лог-файл очищен", "info")
    else:
        flash("⚠️ Лог-файл не найден", "warning")
    return redirect(url_for('main.index'))
