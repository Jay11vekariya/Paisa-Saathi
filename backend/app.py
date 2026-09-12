import logging
import click
from pymongo.errors import PyMongoError
from models.collections import prepare_collections
import os
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from config import Config
from db import init_db, DatabaseUnavailable
from routes import auth, dashboard, transactions, health, analytics, recommendations

def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config:
        app.config.update(config)
    CORS(app, resources={r'/api/*': {'origins': app.config['CORS_ORIGINS']}}, supports_credentials=False)
    init_db(app)
    for module in (auth, dashboard, transactions, health, analytics, recommendations):
        app.register_blueprint(module.bp, url_prefix='/api')

    @app.errorhandler(PyMongoError)
    def mongo_error(error):
        app.logger.warning('MongoDB request unavailable (%s)', type(error).__name__)
        return jsonify(error='Financial data is temporarily unavailable.'), 503

    @app.errorhandler(DatabaseUnavailable)
    def database_error(error):
        return jsonify(error=str(error)), 503

    @app.errorhandler(Exception)
    def handle_error(error):
        if isinstance(error, HTTPException):
            return jsonify(error=error.description), error.code
        app.logger.error('Unhandled request failure (%s)', type(error).__name__)
        return jsonify(error='Something went wrong. Please try again.'), 500
    @app.cli.command('init-db')
    def init_database_command():
        try:
            prepare_collections()
            click.echo('Phase 1 collections are ready.')
        except (DatabaseUnavailable, PyMongoError):
            raise click.ClickException('Database setup failed. Check Atlas configuration and user permissions.') from None
    return app

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    create_app().run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)


