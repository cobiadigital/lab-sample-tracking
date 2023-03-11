from blabel import LabelWriter
from datetime import datetime
import os
import io
from flask import current_app
from cultures.upload import upload_file
from flask import send_file


def makelabel(items):
    label_writer = LabelWriter(os.path.join(current_app.instance_path,'B33-59-0.5x1.html'),
                               default_stylesheets=(os.path.join(current_app.instance_path,'B33-59-0.5x1.css'),))
    records = []
    for item in items:
        records.append(dict(sample_title=item['title'], sample_date=item['date'], sample_comment=item['comment'],
                            sample_lab=item['name'], sample_initials=item['initials'], sample_full_id=item['full_id']))
    filename = datetime.now().strftime("%Y%m%d-%H%M") + 'labels.pdf'
    bytes_pdf = label_writer.write_labels(records)
    label_pdf = io.BytesIO(bytes_pdf)
    return send_file(
        bytes_pdf,
        as_attachment=True,
        download_name=filename,
        mimetype='application/pdf'
    )
    # final_url = upload_file(label_pdf, filename)
    # return final_url
