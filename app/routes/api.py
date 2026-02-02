from flask import Blueprint, jsonify, current_app
from ..services.extractor import get_stream_url
from ..services.scraper_service import scraper_service

api_bp = Blueprint('api', __name__)

@api_bp.route('/scraper/start', methods=['POST'])
def start_scraper():
    # Pass current_app._get_current_object() to thread
    # current_app is a proxy, we need the real app object for app_context
    if scraper_service.start_scrape(current_app._get_current_object()):
        return jsonify({"status": "started"})
    return jsonify({"status": "error", "message": "Already running"}), 400

@api_bp.route('/scraper/stop', methods=['POST'])
def stop_scraper():
    if scraper_service.stop_scrape():
        return jsonify({"status": "stopping"})
    return jsonify({"status": "error", "message": "Not running"}), 400

@api_bp.route('/scraper/status')
def scraper_status():
    return jsonify(scraper_service.get_status())

@api_bp.route('/ping')
def ping():
    return {"status": "pong"}
