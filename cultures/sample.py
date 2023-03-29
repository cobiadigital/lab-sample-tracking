from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for, render_template_string
)
from werkzeug.exceptions import abort
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField, DateTimeField, BooleanField
from flask_wtf.file import FileField, FileRequired, FileAllowed
from werkzeug.utils import secure_filename
from flask import current_app
from dotenv import load_dotenv
import requests
import csv
import io
from flask import send_file
from blabel import LabelWriter

load_dotenv()



import os


from wtforms.validators import DataRequired

from cultures.auth import login_required
from cultures.db import get_db

from cultures.make_labels import makelabel

from datetime import datetime
from cultures.upload import upload_file


bp = Blueprint('sample', __name__)

class CreateForm(FlaskForm):
    title = StringField('Title')
    date = DateTimeField('Date')
    comment = StringField('Comment')
    body = TextAreaField('Body')
    lab = SelectField('Lab', choices=[], validate_choice=True)
    initials = StringField('Initials')
    makeprimary = BooleanField('Make Primary')
    submit = SubmitField('Submit')

class NoteForm(FlaskForm):
    date = DateTimeField('Date')
    body = TextAreaField('New Note')
    lab = SelectField('Lab', choices=[], validate_choice=True)
    initials = StringField('Initials')
    submit = SubmitField('Submit')

class PhotoForm(FlaskForm):
    photo = FileField(validators=[FileRequired()])
    lab = SelectField('Lab', choices=[], validate_choice=True)
    submit = SubmitField('Upload')

class SearchForm(FlaskForm):
    query = StringField('Search Query')
    submit = SubmitField('Submit')


def get_labs():
    db = get_db()
    labs = db.execute(
        'SELECT * FROM lab'
    ).fetchall()
    lab_dict = {key: val for key, date, val in labs}
    return lab_dict

def download_file(pdf, filename):
    return send_file(
        pdf,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )
@bp.route('/', methods=('GET', 'POST'))
def index():
    search_form = SearchForm()
    db = get_db()
    if request.method == 'GET':
        items = db.execute('''
            SELECT s.id, isprimary, s.lab_id, title, comment, s.date, s.body, s.created, s.author_id, 
            email, l.name, s.initials, full_id, transfer_from, n.body as note_body, 
            n.initials as note_initials, n.note_date
            FROM sample s  JOIN user u ON s.author_id = u.id
            JOIN lab l ON s.lab_id = l.id
            LEFT JOIN ( SELECT body, sample_id, initials, max(date) as note_date FROM note
            GROUP BY sample_id ) n ON n.sample_id = s.id
            WHERE s.deleted IS NULL ORDER BY s.created DESC 
            '''
        ).fetchall()
    if request.method == 'POST':
        search_query = search_form.query.data
        items = db.execute('''
            SELECT s.id, isprimary, s.lab_id, title, comment, s.date, s.body, s.created, s.author_id, 
            email, l.name, s.initials, full_id, transfer_from, n.body as note_body, 
            n.initials as note_initials, n.note_date
            FROM sample s  JOIN user u ON s.author_id = u.id
            JOIN lab l ON s.lab_id = l.id
            LEFT JOIN ( SELECT body, sample_id, initials, max(date) as note_date FROM note
            GROUP BY sample_id ) n ON n.sample_id = s.id
            WHERE s.deleted IS NULL AND full_id LIKE ? ORDER BY s.created DESC
            ''', ('%' + search_query + '%',)
        ).fetchall()
        if len(items) == 1:
            return redirect(url_for('sample.single', id=items[0]['id']))
        return render_template('sample/index.html', items=items, search_form=search_form, search_query=search_query)

    return render_template('sample/index.html', items=items, search_form=search_form)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    form = CreateForm()
    lab_dict = get_labs()

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
        isprimary = form.makeprimary.data
        full_id = lab_dict.get(int(lab_id)) + '-' + title + '-'  + date.strftime('%Y%m%d') + '-' + comment + '-' + initials


        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO sample (title, isprimary, date, comment, body, author_id, lab_id, initials, full_id)'
                ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (title, isprimary, date, comment, body, g.user['id'], lab_id, initials, full_id)
            )
            db.commit()
            return redirect(url_for('sample.index'))

    return render_template('sample/create.html', form=form)

def get_sample(id, check_author=True):
    item = get_db().execute(
        '''
         SELECT s.id, title, isprimary, date, comment, body, s.created, name,
        s.initials, s.lab_id, email, full_id, transfer_from, isprimary,
        m.file_url FROM sample s JOIN user u ON s.author_id = u.id
        JOIN  lab l ON s.lab_id = l.id
        LEFT JOIN media m ON m.id = s.primary_image WHERE s.id = ? ''',
        (id,)
    ).fetchone()

    if item is None:
        abort(404, f"Post id {id} doesn't exist.")

    # if check_author and item['author_id'] != g.user['id']:
    #     abort(403)
    return item

def get_note(id):
    note = get_db().execute(
            'SELECT body as note_body, l.name, n.date as note_date, n.initials as note_initials FROM note n JOIN lab l on n.lab_id = l.id WHERE n.id = ?',
            (id,)
        ).fetchone()
    if note is None:
        abort(404, f"Post id {id} doesn't exist.")
    return note

@bp.route('/<int:id>/', methods=('GET', 'POST' ))
def single(id):
    search_form = SearchForm()
    form = NoteForm()
    item = get_sample(id)
    notes = get_db().execute(
        '''
        SELECT n.id as note_id, body as note_body, l.name, n.date as note_date, 
        n.initials as note_initials FROM note n JOIN lab l on n.lab_id = l.id 
        WHERE sample_id = ? AND n.deleted IS NULL ORDER BY n.date DESC ''',
        (id,)
    ).fetchall()
    lab_dict = get_labs()
    form.lab.choices = [(lid, lval) for lid, lval in lab_dict.items()]
    photoform = PhotoForm()
    photoform.lab.choices = form.lab.choices

    if request.method == 'GET':
        form.lab.data = (g.user['lab_id'], g.user['name'])
        photoform.lab.data = (g.user['lab_id'], g.user['name'])
        form.date.data = datetime.now()
        form.initials.data = g.user['initials']

    if request.method == 'POST':
        date = form.date.data
        body = form.body.data
        lab_id = form.lab.data
        initials = form.initials.data
        db = get_db()
        db.execute(
            'INSERT INTO note (date, body, sample_id, author_id, lab_id, initials)'
            ' VALUES (?, ?, ?, ?, ?, ?)',
            (date, body, id, g.user['id'], lab_id, initials,)
        )
        db.commit()
        return redirect(url_for('sample.single', id=id))

    return render_template('sample/single.html', sample_id=id, item=item, notes=notes, form=form, photoform=photoform, search_form=search_form)

@bp.route('/<int:id>/images', methods=( 'POST', ))
@login_required
def sample_images(id):
    db = get_db()
    images = db.execute( '''
       SELECT m.id, sample_id, file_url, s.primary_image FROM media m 
       LEFT JOIN sample s on s.id = m.sample_id WHERE sample_id = ?
         ''',
        (id,)
    ).fetchall()
    return render_template('partials/images.html', images=images)


@bp.route('/<int:id>/<int:sample_id>/make_primary_image', methods=( 'POST', ))
@login_required
def make_primary_image(id, sample_id):
    db = get_db()
    db.execute('UPDATE sample SET primary_image = ? WHERE id = ? ',
               (id, sample_id )
               )
    db.commit()
    item = get_sample(sample_id)
    return render_template('partials/image_return.html', item=item)

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
            full_id = lab_dict.get(int(lab_id)) + '-' + title + '-' + date.strftime(
                '%Y%m%d') + '-' + comment + '-' + initials

            db = get_db()
            db.execute(
                'UPDATE sample SET title = ?, date = ?, comment = ?, lab_id = ?, initials = ?, body = ?, full_id = ?'
                ' WHERE id = ?',
                (title, date, comment, lab_id, initials, body, full_id, id)
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
        form.makeprimary.data = True

    if request.method == 'POST':
        title = form.title.data
        date = form.date.data
        comment = form.comment.data
        lab_id = form.lab.data
        initials = form.initials.data
        body = form.body.data
        makeprimary = form.makeprimary.data

        error = None
        full_id = lab_dict.get(int(lab_id)) + '-' + title + '-' + date.strftime('%Y%m%d') + '-' + comment + '-' + initials

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)

        else:
            if makeprimary == True:
                makeprimaryval = 'Primary'
                db = get_db()
                db.execute(
                    'UPDATE sample SET isprimary = "Backup" WHERE id = ?',
                    (id,)
                )
                db.execute(
                    'UPDATE sample SET isprimary = "Unneeded" WHERE id = ?',
                    (item['transfer_from'],)
                )
                db.execute(
                    'INSERT INTO sample (title, date, comment, body, author_id, lab_id, initials, full_id, '
                    ' transfer_from, isprimary)'
                    ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (title, date, comment, body, g.user['id'], lab_id, initials, full_id, id, makeprimaryval)
                )
                db.commit()
                return redirect(url_for('sample.index'))

            else:
                db = get_db()
                db.execute(
                    'INSERT INTO sample (title, date, comment, body, author_id, lab_id, initials, full_id, transfer_from)'
                    ' VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                    (title, date, comment, body, g.user['id'], lab_id, initials, full_id, id,)
                )
                db.commit()
                return redirect(url_for('sample.index'))

    return render_template('sample/duplicate.html', form=form, item=item)


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

@bp.route('/<int:sample_id>/<int:note_id>/deletenote', methods=('POST',))
@login_required
def delete_note(sample_id, note_id):
    get_note(note_id)
    db = get_db()
    db.execute(
        'UPDATE note SET deleted = CURRENT_TIMESTAMP WHERE id = ?',
        (note_id,))
    db.commit()
    return redirect(url_for('sample.single', id=sample_id))

@bp.route('/<int:id>/makeprimary?transfer_from<int:transfer_from>', methods=('POST',))
@login_required
def makeprimary(id, transfer_from):

    db = get_db()
    db.execute(
        'UPDATE sample SET isprimary = "Primary" WHERE id = ?',
        (id,)
    )
    if transfer_from != 0:
        db.execute(
            'UPDATE sample SET isprimary = "Backup" WHERE id = ?',
            (transfer_from,)
        )
    db.commit()
    return redirect(url_for('sample.single', id=id))

@bp.route('/<int:id>/makebackup', methods=('POST',))
@login_required
def makebackup(id):
    db = get_db()
    db.execute(
        'UPDATE sample SET isprimary = "backup" WHERE id = ?',
        (id,)
    )
    db.commit()
    return redirect(url_for('sample.single', id=id))


@bp.route('/makelabels/', methods=('POST',), defaults={'search_query': None})
@bp.route('/makelabels/<search_query>', methods=('POST',))
@login_required
def makelabels(search_query):
    assert search_query == request.view_args['search_query']
    print(search_query)
    if search_query is not None:
        db = get_db()
        items=db.execute(
                'SELECT s.id, s.lab_id, title, comment, date, body, s.created, author_id, email,'
                ' l.name, s.initials, full_id FROM sample s JOIN user u ON s.author_id = u.id'
                ' JOIN lab l ON s.lab_id = l.id WHERE deleted IS NULL AND full_id LIKE ? ORDER BY s.created DESC ',
                 ('%' + search_query + '%',)
            ).fetchall()
    else:
        db = get_db()
        items = db.execute(
            'SELECT s.id, s.lab_id, title, comment, date, body, s.created, author_id, email,'
            ' l.name, s.initials, full_id FROM sample s JOIN user u ON s.author_id = u.id'
            ' JOIN lab l ON s.lab_id = l.id WHERE deleted IS NULL ORDER BY s.created DESC'
        ).fetchall()
    label_writer = LabelWriter(os.path.join(current_app.instance_path, 'B33-59-0.5x1.html'),
                               default_stylesheets=(os.path.join(current_app.instance_path, 'B33-59-0.5x1.css'),))
    records = []
    for item in items:
        records.append(dict(sample_title=item['title'], sample_date=item['date'], sample_comment=item['comment'],
                            sample_lab=item['name'], sample_initials=item['initials'], sample_full_id=item['full_id']))
    filename = datetime.now().strftime("%Y%m%d-%H%M") + 'labels.pdf'
    bytes_pdf = label_writer.write_labels(records)
    with io.BytesIO(bytes_pdf) as label_pdf:
        download_file(label_pdf, filename)
        print('download complete')
        final_url = upload_file(label_pdf, filename)
        print(final_url)

    # filename = makelabel(items)
    return redirect(url_for('sample.index'))

@bp.route('/make_csv/', methods=('POST',), defaults={'search_query': None})
@bp.route('/make_csv/<search_query>', methods=('POST',))
@login_required
def make_csv(search_query):
    if search_query is not None:
        db = get_db()
        items=db.execute(
            '''
            SELECT s.id, isprimary, s.lab_id, title, comment, s.date, s.body, s.created, s.author_id, 
            email, l.name, s.initials, full_id, transfer_from, n.body as note_body, 
            n.initials as note_initials, n.note_date
            FROM sample s  JOIN user u ON s.author_id = u.id
            JOIN lab l ON s.lab_id = l.id
            LEFT JOIN ( SELECT body, sample_id, initials, max(date) as note_date FROM note
            GROUP BY sample_id ) n ON n.sample_id = s.id
            WHERE s.deleted IS NULL AND full_id LIKE ? ORDER BY s.full_id DESC 
            ''', ('%' + search_query + '%',)
            ).fetchall()
    else:
        db = get_db()
        items=db.execute('''
                SELECT s.id, isprimary, s.lab_id, title, comment, s.date, s.body, s.created, s.author_id, 
                email, l.name, s.initials, full_id, transfer_from, n.body as note_body, 
                n.initials as note_initials, n.note_date
                FROM sample s  JOIN user u ON s.author_id = u.id
                JOIN lab l ON s.lab_id = l.id
                LEFT JOIN ( SELECT body, sample_id, initials, max(date) as note_date FROM note
                GROUP BY sample_id ) n ON n.sample_id = s.id
                WHERE s.deleted IS NULL ORDER BY s.full_id DESC 
                '''
                ).fetchall()

    csv_name = str(datetime.now().strftime('%Y%m%d-%H%M')) + 'samples.csv'

    proxy = io.StringIO()
    writer = csv.writer(proxy)
    writer.writerows(items)
    # Creating the byteIO object from the StringIO Object
    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode())
    # seeking was necessary. Python 3.5.2, Flask 0.12.2
    mem.seek(0)
    proxy.close()
    # download_file(mem, csv_name
    return send_file(
            mem,
            as_attachment=True,
            download_name=csv_name,
            mimetype='text/csv'
        )

@bp.route('/<int:id>/upload', methods=['POST',])
def upload(id):
    form = PhotoForm()
    lab_dict = get_labs()
    form.lab.choices = [(lid, lval) for lid, lval in lab_dict.items()]

    if form.validate_on_submit():
        user_id = g.user['id']
        file = form.photo.data
        print(type(file))
        lab_id = form.lab.data
        filename = secure_filename(file.filename)

        headers = {
            'Authorization': f'Bearer {os.getenv("IMAGE_API")}',
        }
        files = {
            'file': file,
        }
        response = requests.post(
            f"https://api.cloudflare.com/client/v4/accounts/{os.getenv('IMAGE_ACCOUNT_ID')}/images/v1",
            headers=headers, files=files)
        if response.json()['success'] == True:

            print(response.json())
            print(response.json()['result']['variants'])
            file_url = response.json()['result']['variants'][0]
            db = get_db()
            cursor = db.execute(
                'INSERT INTO media (filename, file_url, lab_id, sample_id, user_id)'
                ' VALUES (?, ?, ?, ?, ?)',
                (filename, file_url, lab_id, id, user_id)
            )
            db.commit()
            db = get_db()
            db.execute(
                'UPDATE sample SET primary_image = ? WHERE id = ? ',
                (cursor.lastrowid, id)
            )
            db.commit()
            print('success')
        else:
            print(response.json())
        return redirect(url_for('sample.single', id=id))
