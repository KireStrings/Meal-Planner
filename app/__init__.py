import os
from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from jinja2 import pass_context

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'super-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///spoonacular.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SPOONACULAR_API_KEY'] = os.getenv('SPOONACULAR_API_KEY', 'your-api-key-here')

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
       return User.query.get(int(user_id))
    
    # Register Blueprints
    from .routes.auth import auth
    from .routes.main import main
    from .routes.dashboard import dashboard
    from .routes.browse import browse
    from .routes.meal_plan import meal_plan
    from .routes.dessert_drinks_page import dessert_drinks_page
    from .routes.account import account
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(dashboard)
    app.register_blueprint(browse)
    app.register_blueprint(meal_plan)
    app.register_blueprint(account)

    svg_cache = {}

    @app.template_filter('include_file')
    @pass_context
    def include_file(context, filename):
        if filename in svg_cache:
            return svg_cache[filename]

        path = os.path.join(app.root_path, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                svg_cache[filename] = content
                return content
        except FileNotFoundError:
            return f'<!-- SVG "{filename}" not found -->'

    @app.context_processor
    def inject_current_page():
        return dict(current_page=request.endpoint)
    app.register_blueprint(dessert_drinks_page)

    return app

