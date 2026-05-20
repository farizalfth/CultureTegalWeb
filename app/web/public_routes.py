from flask import Blueprint, render_template
from app.models import CultureSite, Event, UMKM

public_bp = Blueprint('public_bp', __name__)

@public_bp.route('/')
def index():
    return render_template('public/index.html')

@public_bp.route('/jelajah')
def jelajah():
    items = CultureSite.query.order_by(CultureSite.id.desc()).all()
    return render_template('public/jelajah.html', items=items)

@public_bp.route('/event')
def event():
    events = Event.query.order_by(Event.id.desc()).all()
    return render_template('public/event.html', events=events)

@public_bp.route('/umkm')
def umkm_public():
    produks = UMKM.query.order_by(UMKM.id.desc()).all()
    return render_template('public/umkm.html', produks=produks)

@public_bp.route('/tentang')
def tentang():
    return render_template('public/tentang.html')
