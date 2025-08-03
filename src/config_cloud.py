import os
import secrets
from urllib.parse import urlparse

class CloudConfig:
    """Configuração automática para deploy em nuvem"""
    
    def __init__(self):
        self.detect_platform()
        self.setup_database()
        self.setup_security()
    
    def detect_platform(self):
        """Detecta a plataforma de deploy automaticamente"""
        if os.environ.get('RAILWAY_ENVIRONMENT'):
            self.platform = 'railway'
        elif os.environ.get('RENDER'):
            self.platform = 'render'
        elif os.environ.get('DYNO'):
            self.platform = 'heroku'
        elif os.environ.get('VERCEL'):
            self.platform = 'vercel'
        elif os.environ.get('PYTHONANYWHERE_DOMAIN'):
            self.platform = 'pythonanywhere'
        else:
            self.platform = 'local'
    
    def setup_database(self):
        """Configura banco de dados baseado na plataforma"""
        database_url = os.environ.get('DATABASE_URL')
        
        if database_url:
            # Corrigir URL do PostgreSQL para SQLAlchemy
            if database_url.startswith('postgres://'):
                database_url = database_url.replace('postgres://', 'postgresql://', 1)
            self.database_url = database_url
        else:
            # Fallback para SQLite local
            self.database_url = 'sqlite:///pesquisa_transporte.db'
    
    def setup_security(self):
        """Configura chaves de segurança"""
        self.secret_key = os.environ.get('SECRET_KEY') or secrets.token_urlsafe(32)
        self.debug = os.environ.get('FLASK_ENV') != 'production'
    
    def get_config(self):
        """Retorna configuração completa"""
        return {
            'SECRET_KEY': self.secret_key,
            'SQLALCHEMY_DATABASE_URI': self.database_url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'DEBUG': self.debug,
            'PLATFORM': self.platform,
            'PORT': int(os.environ.get('PORT', 5000))
        }

# Instância global da configuração
cloud_config = CloudConfig()
config = cloud_config.get_config()

# Configurações específicas por plataforma
PLATFORM_CONFIGS = {
    'railway': {
        'CORS_ORIGINS': ['*'],
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,  # 16MB
        'PERMANENT_SESSION_LIFETIME': 3600,
    },
    'render': {
        'CORS_ORIGINS': ['*'],
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,
        'PERMANENT_SESSION_LIFETIME': 3600,
        'SEND_FILE_MAX_AGE_DEFAULT': 31536000,  # Cache 1 ano
    },
    'heroku': {
        'CORS_ORIGINS': ['*'],
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,
        'PERMANENT_SESSION_LIFETIME': 3600,
    },
    'pythonanywhere': {
        'CORS_ORIGINS': ['*'],
        'MAX_CONTENT_LENGTH': 8 * 1024 * 1024,  # 8MB (menor para free)
        'PERMANENT_SESSION_LIFETIME': 1800,  # 30min
    },
    'local': {
        'CORS_ORIGINS': ['http://localhost:3000', 'http://127.0.0.1:3000'],
        'MAX_CONTENT_LENGTH': 16 * 1024 * 1024,
        'PERMANENT_SESSION_LIFETIME': 3600,
    }
}

# Aplicar configurações específicas da plataforma
platform_config = PLATFORM_CONFIGS.get(cloud_config.platform, PLATFORM_CONFIGS['local'])
config.update(platform_config)

def get_database_url():
    """Retorna URL do banco configurada"""
    return config['SQLALCHEMY_DATABASE_URI']

def get_platform():
    """Retorna plataforma detectada"""
    return config['PLATFORM']

def is_production():
    """Verifica se está em produção"""
    return not config['DEBUG']

def get_port():
    """Retorna porta configurada"""
    return config['PORT']
