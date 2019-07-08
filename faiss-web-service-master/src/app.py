from flask import Flask

from internal.blueprint import blueprint as InternalBlueprint
from faiss_index.blueprint import create_db as CreatedbBlueprint

app = Flask(__name__)

app.register_blueprint(InternalBlueprint)
app.register_blueprint(CreatedbBlueprint)

# The ip address defaults to localhost
if __name__ == "__main__":
    app.run(host="0.0.0.0")
