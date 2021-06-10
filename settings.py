import os

DATABASE_URI = os.environ.get("DATABASE_URI") or 'sqlite:////tmp/mdt-publisher.db'
TRACK_MODIFICATIONS = False
