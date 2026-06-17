from app import create_app, db
from app.models import CultureSite, Review

app = create_app()
with app.app_context():
    Review.query.delete()
    
    db.session.execute(db.text("DELETE FROM culture_facilities"))
    
    CultureSite.query.delete()
    
    db.session.commit()
    print("Database berhasil dibersihkan sepenuhnya!")