# ------------------------------------------------------------------
# pyinstaller --add-data "templates;templates" --add-data "static;static" --add-data "blueprints/promotions;blueprints/promotions" AttendancePromotions.py
# pyinstaller --add-data "templates:templates" --add-data "static:static" --add-data "blueprints/promotions:blueprints/promotions" AttendancePromotions.py
# ------------------------------------------------------------------

import os
import sys
from tkinter import messagebox

import tkinter as tk
from flask import Flask, render_template, request, jsonify, redirect, url_for, Blueprint
from flask_htmx import HTMX
from flaskwebgui import FlaskUI

from sqlalchemy.orm import Session

import constants
from blueprints.promotions.promotions_routes import promotions_bp
from services.processScanner import DisplayActiveProcesses, IsProcessActive
from sqlite.sqlite_alchemy import getAlchemySession, listDbSessions

# ----------------------------------------------------------------------------------
base_dir = '.'
if hasattr(sys, '_MEIPASS'):
    base_dir = os.path.join(sys._MEIPASS)

# ----------------------------------------------------------------------------------
app = Flask(__name__, static_folder=os.path.join(base_dir, 'static'), template_folder=os.path.join(base_dir, 'templates'))
app.register_blueprint(promotions_bp)

htmx = HTMX(app)

# ----------------------------------------------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('promotions_bp.promotions_bp_home'))
    #return render_template('index.html')

# ----------------------------------------------------------------------------------
@app.errorhandler(404)
@app.errorhandler(500)
def page_not_found(e):
    missing_url = None
    try:
        if request is not None:
            missing_url = request.url
    except Exception as ex:
        print(f'exception:{ex}')
    app.logger.error(f"page_not_found:{e}\n{missing_url}")
    if missing_url is None:
        return render_template("error.html",message="Page not found")
    else:
        return render_template("error.html",message="Page not found", original_message=missing_url)

# ----------------------------------------------------------------------------------
def CheckDbConnection(db_name: str) -> Session:
    temp_session = getAlchemySession(db_name)
    print(f'{temp_session.bind.url.database}')
    return temp_session

if __name__ == '__main__':
    DisplayActiveProcesses('attendance')
    ok_to_start = IsProcessActive(constants.applicationName)
    if ok_to_start['status'] == 'ok':
        ui = FlaskUI(app=app, width=1250, height=900, fullscreen=False, server='flask', port=5002)
        ui.run()
    else:
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo("Attendance Promotions - Error", ok_to_start['message'])
        print(ok_to_start['message'])
    #app.run(debug=False,  port=5002)



