from blabel import LabelWriter
from datetime import datetime
import os
import io
from flask import current_app
from cultures.upload import upload_pdf


def makelabel(items):
    label_writer = LabelWriter(os.path.join(current_app.instance_path,'B33-59-0.5x1.html'),
                               default_stylesheets=(os.path.join(current_app.instance_path,'B33-59-0.5x1.css'),))
    records = []
    for item in items:
        print(item['title'])
        records.append(dict(sample_title=item['title'], sample_date=item['date'], sample_comment=item['comment'],
                            sample_lab=item['name'], sample_initials=item['initials'], sample_full_id=item['full_id']))
    filename = datetime.now().strftime("%Y%m%d-%H%M") + 'labels.pdf'
    bytes_pdf = label_writer.write_labels(records)
    print(type(bytes_pdf))
    label_pdf = io.BytesIO(bytes_pdf)
    print(type(label_pdf))
    final_url = upload_pdf(label_pdf, filename)

    return final_url
