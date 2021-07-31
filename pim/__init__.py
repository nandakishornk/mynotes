import os
import random

from flask import Flask, render_template

from . import db

def create_app(test_config=None) :
  app = Flask("pim")
  app.config["SECRET_KEY"] = "this is a secret key"
  app.config.from_mapping(DATABASE=os.path.join(app.instance_path, 'pim.sqlite'))

  if test_config is not None:
        app.config.update(test_config)

  try:
        os.makedirs(app.instance_path)
  except OSError:
        pass
  
  from . import pim
  app.register_blueprint(pim.bp)
    
  from . import db
  db.init_app(app)
  
  
  return app
