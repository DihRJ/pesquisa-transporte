import os
import sys
from datetime import timedelta
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_mail import Mail

# Importar instância única do banco de dados
from src.database import db
from src.config_cloud import get_database_url

# Importar todos os modelos
from src.models.user import User
from src.models.pesquisa import Pesquisa, ContadorLinha
from src.models.usuario import Usuario
from src.models.relatorio import Relatorio

# Importar rotas
from src.routes.user import user_bp
from src.routes.pesquisa import pesquisa_bp
from src.routes.auth import auth_bp
from src.routes.relatorios import relatorios_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Configurar sessões
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Configurar CORS
CORS(app, supports_credentials=True)

# Configurar Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sistema.pesquisa.transporte@gmail.com'
app.config['MAIL_PASSWORD'] = 'senha_do_email'  # Em produção, usar variável de ambiente
app.config['MAIL_DEFAULT_SENDER'] = 'sistema.pesquisa.transporte@gmail.com'

mail = Mail(app)

# Disponibilizar mail globalmente
app.mail = mail

# Registrar blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(pesquisa_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(relatorios_bp, url_prefix='/api')

# Configurar banco de dados
# Configure the SQLAlchemy database URI using the cloud-aware configuration.
# This will use the DATABASE_URL environment variable when running on Render and
# fall back to a local SQLite database when no DATABASE_URL is provided.
app.config['SQLALCHEMY_DATABASE_URI'] = get_database_url()
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar banco de dados único
db.init_app(app)

with app.app_context():
    db.create_all()
    
    # Criar usuário administrador padrão
    Usuario.criar_admin_padrao()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    # Rotas específicas
    if path == 'login':
        return send_from_directory(static_folder_path, 'login.html')
    elif path == 'admin':
        return send_from_directory(static_folder_path, 'admin.html')
    elif path == 'relatorios':
        return send_from_directory(static_folder_path, 'relatorios.html')
    elif path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

