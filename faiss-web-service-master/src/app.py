from flask import Flask

from internal.blueprint import blueprint as InternalBlueprint
from faiss_index.blueprint import create_db as CreatedbBlueprint

app = Flask(__name__)
# app.config.from_object('config')
# app.config.from_envvar('FAISS_WEB_SERVICE_CONFIG')

app.register_blueprint(InternalBlueprint)
app.register_blueprint(CreatedbBlueprint)

if __name__ == "__main__":
    app.run(host="0.0.0.0")
