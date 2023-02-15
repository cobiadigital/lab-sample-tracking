from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, render_template_string
)
from werkzeug.exceptions import abort
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateTimeField
from wtforms.validators import DataRequired

from cultures.auth import login_required
from cultures.db import get_db

from cultures.make_labels import makelabel

from datetime import datetime
from cultures.upload import upload_pdf


bp = Blueprint('sample', __name__)

class CreateForm(FlaskForm):
    title = StringField('title')
    date = DateTimeField('date')
    comment = StringField('comment')
    body = TextAreaField('body')
    lab = SelectField('lab', choices=[], validate_choice=True)
    initials = StringField('initials')
    submit = SubmitField('Submit')

class NoteForm(FlaskForm):
    date = DateTimeField('Date')
    body = TextAreaField('Body')
    lab = SelectField('Lab', choices=[], validate_choice=True)
    initials = StringField('Initials')
    submit = SubmitField('Submit')

def get_labs():
    db = get_db()
    labs = db.execute(
        'SELECT * FROM lab'
    ).fetchall()
    lab_dict = {key: val for key, date, val in labs}
    return lab_dict

@bp.route('/')
def index():
    db = get_db()
    items = db.execute(
        'SELECT s.id, s.lab_id, title, comment, date, body, s.created, author_id, email, '
        ' l.name, s.initials, full_id, transfer_from, note_body, note_initials, note_date, note_lab_id '
        'FROM sample s  JOIN user u ON s.author_id = u.id '
        'JOIN lab l ON s.lab_id = l.id '
        'JOIN( SELECT note_body, note_date, note_lab_id, sample_id, note_initials  '
        '    from note ORDER BY note_date DESC LIMIT 1 '
        ' ) n  ON n.sample_id = s.id WHERE deleted IS NULL ORDER BY s.created DESC'
    ).fetchall()
    return render_template('sample/index.html', items=items)

@bp.route('/htmx/')
def index2():
    db = get_db()
    items = db.execute(
        'SELECT s.id, s.lab_id, title, comment, date, body, s.created, author_id, email, '
        ' l.name, s.initials, full_id, transfer_from, note_body, note_initials, note_date, note_lab_id '
        'FROM sample s  JOIN user u ON s.author_id = u.id '
        'JOIN lab l ON s.lab_id = l.id '
        'JOIN( SELECT note_body, note_date, note_lab_id, sample_id, note_initials  '
        '    from note ORDER BY note_date DESC LIMIT 1 '
        ' ) n  ON n.sample_id = s.id WHERE deleted IS NULL ORDER BY s.created DESC'
    ).fetchall()
    return render_template('sample/index2.html', items=items)

def searching(self, word):
    if (word is None):
        return False
    return word.lower() in self.title.lower()

@app.route('/results')
def search_results(search):
    results = []
    search_string = search.data['search']
    if search.data['search'] == '':
        qry = db_session.query(Album)
        results = qry.all()
    if not results:
        flash('No results found!')
        return redirect('/')
    else:
        # display results
        return render_template('results.html', results=results)

@bp.route('/search', methods=('POST'))
def search():
    db = get_db()
    items = db.execute(
        'SELECT s.id, s.lab_id, title, comment, date, body, s.created, author_id, email, '
        ' l.name, s.initials, full_id, transfer_from, note_body, note_initials, note_date, note_lab_id '
        'FROM sample s  JOIN user u ON s.author_id = u.id '
        'JOIN lab l ON s.lab_id = l.id '
        'JOIN( SELECT note_body, note_date, note_lab_id, sample_id, note_initials  '
        '    from note ORDER BY note_date DESC LIMIT 1 '
        ' ) n  ON n.sample_id = s.id WHERE deleted IS NULL ORDER BY s.created DESC'
    ).fetchall()
    searchWord = request.form.get('search', None)
    matchsample = [item in item in items if searching(searchWord)]
    return render_template('partials/results.html', items=matchsample)


@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = CreateForm()
    lab_dict = get_labs()
    print(lab_dict)
    print(type(lab_dict))

    # for lab in labs:
    #     lab_dict[lab['id']].append(name)

    if request.method == 'GET':
        form.lab.choices = [(lid, lval) for lid, lval in lab_dict.items()]
        form.lab.data = (g.user['lab_id'], g.user['name'])
        form.date.data = datetime.now()
        form.initials.data = g.user['initials']

    if request.method == 'POST':
        title = form.title.data
        date = form.date.data
        comment = form.comment.data
        lab_id = form.lab.data
        initials = form.initials.data
        body = form.body.data
        full_id = labs.get(int(lab_id)) + '-' + title + '-'  + date.strftime('%Y%m%d') + '-' + comment + '-' + initials


        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO sample (title, date, comment, body, author_id, lab_id, initials, full_id)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (title, date, comment, body, g.user['id'], lab_id, initials, full_id)
            )
            db.commit()
            return redirect(url_for('sample.index'))

    return render_template('sample/create.html', form=form)

def get_sample(id, check_author=True):
    item = get_db().execute(
        'SELECT s.id, title, date, comment, body, s.created, name, s.initials, s.lab_id, '
        'email, full_id, transfer_from FROM sample s JOIN user u ON s.author_id = u.id '
        ' JOIN lab l ON s.lab_id = l.id WHERE s.id = ? ',
        (id,)
    ).fetchone()

    if item is None:
        abort(404, f"Post id {id} doesn't exist.")

    # if check_author and item['author_id'] != g.user['id']:
    #     abort(403)

    return item

@bp.route('/<int:id>/', methods=('GET', 'POST' ))
def single(id):
    form = NoteForm()
    item = get_sample(id)
    notes = get_db().execute(
        'SELECT note_body, l.name, note_date, note_initials FROM note n JOIN lab l on n.note_lab_id = l.id WHERE sample_id = ? ORDER BY note_date DESC',
        (id,)
    ).fetchall()
    lab_dict = get_labs()
    form.lab.choices = [(lid, lval) for lid, lval in lab_dict.items()]
    if request.method == 'GET':
        form.lab.data = (g.user['lab_id'], g.user['name'])
        form.date.data = datetime.now()
        form.initials.data = g.user['initials']

    if request.method == 'POST':
        date = form.date.data
        body = form.body.data
        lab_id = form.lab.data
        initials = form.initials.data
        db = get_db()
        db.execute(
            'INSERT INTO note (note_date, note_body, sample_id, author_id, lab_id, note_initials)'
            ' VALUES (?, ?, ?, ?, ?, ?)',
            (date, body, id, g.user['id'], lab_id, initials,)
        )
        db.commit()
        return redirect(url_for('sample.single', id=id))

    return render_template('sample/single.html', item=item, notes=notes, form=form)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    form = CreateForm()
    item = get_sample(id)
    lab_dict = get_labs()
    if request.method == 'GET':
        form.title.data = item['title']
        form.date.data = item['date']
        form.comment.data = item['comment']
        form.lab.choices = [(lid, lval) for lid, lval in lab_dict.items()]
        form.lab.data = (item['lab_id'], item['name'])
        form.initials.data = item['initials']
        form.body.data = item['body']

    if request.method == 'POST':
        title = form.title.data
        date = form.date.data
        comment = form.comment.data
        lab_id = form.lab.data
        initials = form.initials.data
        body = form.body.data
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE sample SET title = ?, date = ?, comment = ?, lab_id = ?, initials = ?, body = ?'
                ' WHERE id = ?',
                (title, date, comment, lab_id, initials, body, id)
            )
            db.commit()
            return redirect(url_for('sample.index'))

    return render_template('sample/update.html', form=form, item=item)

@bp.route('/<int:id>/duplicate', methods=('GET', 'POST'))
@login_required
def duplicate(id):
    lab_dict = get_labs()
    form = CreateForm()
    item = get_sample(id)
    if request.method == 'GET':
        form.title.data = item['title']
        form.date.data = datetime.now()
        form.comment.data = item['comment']
        form.lab.choices = [(lid, lval) for lid, lval in lab_dict.items()]
        form.lab.data = (g.user['lab_id'], g.user['name'])
        form.initials.data = g.user['initials']
        form.body.data = item['body']

    if request.method == 'POST':
        title = form.title.data
        date = form.date.data
        comment = form.comment.data
        lab_id = form.lab.data
        initials = form.initials.data
        body = form.body.data
        error = None
        full_id = lab_dict.get(int(lab_id)) + '-' + title + '-' + date.strftime('%Y%m%d') + '-' + comment + '-' + initials

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO sample (title, date, comment, body, author_id, lab_id, initials, full_id, transfer_from)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (title, date, comment, body, g.user['id'], lab_id, initials, full_id, id)
            )
            db.commit()
            return redirect(url_for('sample.index'))

    return render_template('sample/update.html', form=form, item=item)


@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_sample(id)
    db = get_db()
    db.execute(
        'UPDATE sample SET deleted = CURRENT_TIMESTAMP WHERE id = ?',
        (id,))
    db.commit()
    return redirect(url_for('sample.index'))

@bp.route('/makelabels', methods=('POST',))
@login_required
def makelabels():
    db = get_db()
    items=db.execute(
            'SELECT s.id, s.lab_id, title, comment, date, body, s.created, author_id, email,'
            ' l.name, s.initials, full_id FROM sample s JOIN user u ON s.author_id = u.id'
            ' JOIN lab l ON s.lab_id = l.id WHERE deleted IS NULL ORDER BY s.created DESC'
    ).fetchall()
    filename = makelabel(items)
    #upload_pdf(filename)
    print(filename)
    return redirect(url_for('sample.index'))