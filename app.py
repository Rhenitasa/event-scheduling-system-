from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from models import db, Event, Resource, Allocation
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///events.db'
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return redirect('/events')

# EVENTS
@app.route('/events')
def events():
    return render_template('events.html', events=Event.query.all())

@app.route('/add-event', methods=['GET','POST'])
def add_event():
    if request.method == 'POST':
        event = Event(
            title=request.form['title'],
            start_time=datetime.fromisoformat(request.form['start']),
            end_time=datetime.fromisoformat(request.form['end']),
            description=request.form['desc']
        )
        db.session.add(event)
        db.session.commit()
        return redirect('/events')
    return render_template('add_event.html')

@app.route('/edit-event/<int:id>', methods=['GET', 'POST'])
def edit_event(id):
    event = Event.query.get(id)

    if request.method == 'POST':
        event.title = request.form['title']
        event.start_time = datetime.fromisoformat(request.form['start'])
        event.end_time = datetime.fromisoformat(request.form['end'])
        event.description = request.form['desc']
        db.session.commit()
        return redirect('/events')

    return render_template('edit_event.html', event=event)


# RESOURCES
@app.route('/resources')
def resources():
    return render_template('resources.html', resources=Resource.query.all())

@app.route('/add-resource', methods=['GET','POST'])
def add_resource():
    if request.method == 'POST':
        res = Resource(
            name=request.form['name'],
            type=request.form['type']
        )
        db.session.add(res)
        db.session.commit()
        return redirect('/resources')
    return render_template('add_resource.html')

@app.route('/edit-resource/<int:id>', methods=['GET', 'POST'])
def edit_resource(id):
    resource = Resource.query.get(id)

    if request.method == 'POST':
        resource.name = request.form['name']
        resource.type = request.form['type']
        db.session.commit()
        return redirect('/resources')

    return render_template('edit_resource.html', resource=resource)


# ALLOCATION + CONFLICT CHECK
def has_conflict(resource_id, start, end):
    allocations = Allocation.query.filter_by(resource_id=resource_id).all()
    for alloc in allocations:
        event = Event.query.get(alloc.event_id)
        if start < event.end_time and end > event.start_time:
            return True
    return False

@app.route('/allocate', methods=['GET','POST'])
def allocate():
    if request.method == 'POST':
        event = Event.query.get(int(request.form['event']))
        resource_id = int(request.form['resource'])

        if has_conflict(resource_id, event.start_time, event.end_time):
            flash("❌ Resource already booked during this time")
        else:
            db.session.add(Allocation(event_id=event.id, resource_id=resource_id))
            db.session.commit()
            flash("✅ Resource allocated successfully")
    return render_template(
        'allocate.html',
        events=Event.query.all(),
        resources=Resource.query.all()
    )

# REPORT
@app.route('/report')
def report():
    data = []
    for res in Resource.query.all():
        hours = 0
        upcoming = []
        for alloc in Allocation.query.filter_by(resource_id=res.id):
            event = Event.query.get(alloc.event_id)
            hours += (event.end_time - event.start_time).seconds / 3600
            upcoming.append(event.title)
        data.append((res.name, hours, upcoming))
    return render_template('report.html', data=data)

app.run(debug=True)
