"""WSGI entry point; importing this file does not start a server or initialize data."""
from app import create_app

application = create_app()

