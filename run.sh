./venv/bin/activate

uwsgi --socket :61116 --wsgi-file ./SiriusSite/wsgi.py --enable-threads