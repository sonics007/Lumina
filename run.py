from app import create_app

app = create_app()

if __name__ == '__main__':
    # Disable SSL warnings mainly for scraper
    import urllib3
    urllib3.disable_warnings()
    
    import logging
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )
    
    # Run
    logging.info("Starting APP with SQLite architecture on port 5001...")
    app.run(host='0.0.0.0', port=5001, debug=True)
