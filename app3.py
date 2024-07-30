from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
from ping3 import ping
from datetime import datetime
import requests
from functools import wraps
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'Roumaissa'

# Liste des adresses IP des machines à surveiller
machines = [
    

def format_time(seconds):
    if seconds is None or seconds == '':
        return '0j 0h 0m 0s'
    try:
        seconds = int(seconds)
    except ValueError:
        return '0j 0h 0m 0s'
    days = seconds // 86400
    seconds %= 86400
    hours = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    return f'{days}j {hours}h {minutes}m {seconds}s'
app.jinja_env.filters['format_time'] = format_time
def check_machine_status(host):
    response_time = ping(host)
    if response_time is None:
        return "offline"
    elif response_time < 100:
        return "online"
    else:
        return "unknown"

#les focntions pour l'histroriaque:
def save_machine_status(devices):
    today = datetime.today().strftime('%Y-%m-%d')
    filename = f"history_{today}.json"

    # Si le fichier existe, chargez les données existantes
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            history = json.load(file)
    else:
        history = []

    # Créez un dictionnaire pour les machines avec leur état actuel
    current_status = {device['host']: device for device in devices}

    # Mettre à jour les états des machines existantes ou ajouter de nouvelles entrées
    updated_history = []
    for entry in history:
        host = entry['host']
        if host in current_status:
            entry['status'] = current_status[host]['status']
            entry['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            updated_history.append(entry)
            current_status.pop(host)
        else:
            updated_history.append(entry)

    # Ajouter les nouvelles machines
    for device in current_status.values():
        updated_history.append({
            "device": device["device"],
            "host": device["host"],
            "status": device["status"],
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    # Sauvegarder l'historique mis à jour dans le fichier
    with open(filename, 'w') as file:
        json.dump(updated_history, file, indent=4)

def load_history():
    history = []
    for filename in os.listdir('.'):
        if filename.startswith('history_') and filename.endswith('.json'):
            with open(filename, 'r') as file:
                day_history = json.load(file)
                history.extend(day_history)
    return history



#le login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Veuillez vous connecter pour accéder à cette page', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function
@app.route('/')
@login_required
def index():
    # Collecter les données sur les machines
    devices = []
    for machine in machines:
        status = check_machine_status(machine["host"])
        devices.append({
            "device": machine["device"],
            "host": machine["host"],
            "status": status,
            "downtimesince": 0 
        })
    # Sauvegarder les états des machines
    save_machine_status(devices)

    total_offline = sum(1 for d in devices if d["status"] == "offline")
    total_unknown = sum(1 for d in devices if d["status"] == "unknown")
    total_paused = 0
    total_devices = len(devices)

    return render_template('index.html', devices=devices,
                            total_offline=total_offline,
                            total_unknown=total_unknown,
                            total_paused=total_paused,
                            total_devices=total_devices)
users = {
    'admin': '123',
    'user1': 'mypassword'
}

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            flash('Vous êtes maintenant connecté!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash('Vous êtes maintenant déconnecté!', 'success')
    return redirect(url_for('login'))

@app.route('/historique')
@login_required
def historique():
    historique_entries = load_history()
    return render_template('historique.html', historique_entries=historique_entries)
if __name__ == '__main__':
    app.run(debug=True)