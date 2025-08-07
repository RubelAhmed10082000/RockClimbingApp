from flask import Flask
from flask_caching import Cache

app = Flask(__name__)
cache = Cache(app, config={'CACHE_TYPE':'SimpleCache', 'CACHE_DEFAULT_TIMEOU': 18000})

from app.routes import routes
routes.cache = cache