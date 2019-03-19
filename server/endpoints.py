# -*- encoding: UTF-8 -*-

import os

import google.oauth2.credentials
import google_auth_oauthlib.flow

from .middlewares import login_required
from flask import Flask, json, g, request, session, url_for, redirect
from .db.service import Service
from flask_cors import CORS

import server.platforms.utils.util as util
from server.scripts.data_sync import DataSync
from server.workflow.tasks.whitepaper_journal.event_poster import WhitepaperJournalEventPoster

app = Flask(__name__)
app.secret_key = 'Octopus: Star of Smart Media'
CORS(app)

REDIRECT_URL = 'https://206.189.161.176:8080/googleredirect'

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.yaml')
config = util.load_yaml(CONFIG_PATH)


@app.route("/googleredirect", methods=["GET"])
def oauth2callback():
    settings = config['google']
    state = session['state']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        settings['creds_file'], scopes=settings['scopes'], state=state)
    flow.redirect_uri = url_for('googleredirect', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'token_uri': credentials.token_uri,
        'client_id': credentials.client_id,
        'client_secret': credentials.client_secret,
        'scopes': credentials.scopes}
    redirect(url_for(state))


@app.route("/googleauthorize", methods=["GET"])
def authorize():
    settings = config['google']
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        settings['creds_file'], scopes=settings['scopes'])
    flow.redirect_uri = REDIRECT_URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true')
    return redirect(authorization_url)


@app.route("/refresh", methods=["POST"])
@login_required
def refresh():
    DataSync(config).sync()
    return json_response({'success': True})


@app.route("/schedule", methods=["POST"])
@login_required
def schedule():
    return json_response({'success': True})


@app.route("/event_poster/<int:session_id>", methods=["GET"])
@login_required
def event_poster(session_id):
    if 'credentials' not in session:
        return redirect('googleauthorize')
    creds = google.oauth2.credentials.Credentials(
        **session['credentials'])
    poster_generator = WhitepaperJournalEventPoster(creds)
    poster_generator.process(session_id)
    return json_response({'success': True})


@app.route("/sessions", methods=["GET"])
@login_required
def index():
    return json_response(Service(config['mongo']).get_recent_sessions())


@app.route("/session/<int:session_id>", methods=["GET"])
@login_required
def show(session_id):
    return json_response(Service(config['mongo']).get_session(session_id))


@app.route("/presenter/<username>", methods=["GET"])
@login_required
def presenter(username):
    return json_response(Service(config['mongo']).get_presenter(username))


def json_response(payload, status=200):
    return (json.dumps(payload), status, {'content-type': 'application/json'})
