import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'citation-builder-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(os.path.dirname(basedir), 'instance', 'citation.db')
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PLAYWRIGHT_HEADLESS = os.environ.get('PLAYWRIGHT_HEADLESS', 'true').lower() == 'true'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(basedir), 'uploads')
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600
    DIRECTORIES_DATA_PATH = os.path.join(basedir, 'data', 'ca_directories.json')
