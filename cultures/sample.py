from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
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


@bp.route('/')
def index():
    db = get_db()
    items = db.execute(
        'SELECT s.id, s.lab_id, title, comment, date, body, s.created, author_id, email,'
        ' l.name, s.initials, full_id FROM sample s JOIN user u ON s.author_id = u.id'
        ' JOIN lab l ON s.lab_id = l.id ORDER BY s.created DESC'
    ).fetchall()
    return render_template('sample/index.html', items=items)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = CreateForm()
    db = get_db()
    labs = db.execute(
        'SELECT * FROM lab'
    ).fetchall()
    lab_id_lst = [(lab['id']) for lab in labs]
    lab_name_lst = [(lab['name']) for lab in labs]
    i = 0
    lab_dict = dict.fromkeys(lab_id_lst)

    lab_dict = {}
    for key in lab_id_lst:
        for value in lab_name_lst:
            lab_dict[key] = value
            break

    # for lab in labs:
    #     lab_dict[lab['id']].append(name)

    if request.method == 'GET':
        form.lab.choices = [(lab['id'], lab['name']) for lab in labs]
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
        full_id = lab_dict.get(int(lab_id)) + '-' + title + '-'  + date.strftime('%Y%m%d') + '-' + comment + '-' + initials


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
        'SELECT s.id, title, date, comment, body, s.created, name, s.initials, s.lab_id, name, email'
        ' FROM sample s JOIN user u ON s.author_id = u.id '
        ' JOIN lab l ON s.lab_id = l.id '
        ' WHERE s.id = ?',
        (id,)
    ).fetchone()

    if item is None:
        abort(404, f"Post id {id} doesn't exist.")

    # if check_author and item['author_id'] != g.user['id']:
    #     abort(403)

    return item

@bp.route('/<int:id>/', methods=('GET', ))
def single(id):
    item = get_sample(id)
    return render_template('sample/single.html', item=item)


@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):

    form = CreateForm()
    item = get_sample(id)
    if request.method == 'GET':
        db = get_db()
        labs = db.execute(
            'SELECT * FROM lab'
        ).fetchall()
        form.title.data = item['title']
        form.date.data = item['date']
        form.comment.data = item['comment']
        form.lab.choices = [(lab['id'], lab['name']) for lab in labs]
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

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_sample(id)
    db = get_db()
    db.execute('DELETE FROM sample WHERE id = ?', (id,))
    db.commit()
    return redirect(url_for('sample.index'))

@bp.route('/makelabels', methods=('POST',))
@login_required
def makelabels():
    db = get_db()
    items=db.execute(
            'SELECT s.id, s.lab_id, title, comment, date, body, s.created, author_id, email,'
            ' l.name, s.initials, full_id FROM sample s JOIN user u ON s.author_id = u.id'
            ' JOIN lab l ON s.lab_id = l.id ORDER BY s.created DESC'
    ).fetchall()
    filename = makelabel(items)
    #upload_pdf(filename)
    print(filename)
    return redirect(url_for('sample.index'))