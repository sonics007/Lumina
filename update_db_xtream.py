from app import create_app, db
from app.models import XtreamUser

app = create_app()

with app.app_context():
    db.create_all()
    
    # Create default admin if not exists
    if not XtreamUser.query.filter_by(username='admin').first():
        print("Creating default admin user...")
        admin = XtreamUser(username='admin', password='admin', max_connections=999)
        db.session.add(admin)
        db.session.commit()
        print("Done.")
    else:
        print("Admin verified.")
