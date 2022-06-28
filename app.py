from flask_migrate import Migrate
from oas.manager import app, db

Migrate(app, db)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, use_reloader=False)
