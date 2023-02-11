from blabel import LabelWriter
from datetime import datetime
import os
from flask import current_app

def makelabel(items):
    os.path.join(current_app.instance_path, 'my_file.txt')
    label_writer = LabelWriter(os.path.join(current_app.instance_path,'B33-59-0.5x1.html'),
                               default_stylesheets=(os.path.join(current_app.instance_path,'B33-59-0.5x1.css'),))
    records = []

    for item in items:
        print(item['title'])
        records.append(dict(sample_title=item['title'], sample_date=item['date'], sample_comment=item['comment'],
                            sample_lab=item['name'], sample_initials=item['initials'], sample_full_id=item['full_id']))


    filename = datetime.now().strftime("%Y%m%d") + 'labels.pdf'
    label_writer.write_labels(records, target=filename)
    return filename