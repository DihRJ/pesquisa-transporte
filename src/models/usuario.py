from src.database import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import secrets

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    nome = db.Column(db.String(100), nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    # Use local time when creating users to respect the configured TZ
    data_criacao = db.Column(db.DateTime, default=datetime.now, nullable=False)
    ultimo_login = db.Column(db.DateTime)
    token_sessao = db.Column(db.String(255), unique=True)
    
    def __init__(self, email, nome, senha, is_admin=False):
        self.email = email.lower().strip()
        self.nome = nome.strip()
        self.senha_hash = generate_password_hash(senha)
        self.is_admin = is_admin
        self.token_sessao = secrets.token_urlsafe(32)
    
    def verificar_senha(self, senha):
        """Verifica se a senha fornecida está correta"""
        return check_password_hash(self.senha_hash, senha)
    
    def alterar_senha(self, nova_senha):
        """Altera a senha do usuário"""
        self.senha_hash = generate_password_hash(nova_senha)
        self.token_sessao = secrets.token_urlsafe(32)  # Invalida sessões existentes
    
    def fazer_login(self):
        """Registra o login do usuário usando o horário local"""
        # Use local time instead of UTC for login timestamps
        self.ultimo_login = datetime.now()
        self.token_sessao = secrets.token_urlsafe(32)
    
    def to_dict(self):
        """Converte o usuário para dicionário (sem dados sensíveis)"""
        return {
            'id': self.id,
            'email': self.email,
            'nome': self.nome,
            'is_admin': self.is_admin,
            'ativo': self.ativo,
            'data_criacao': self.data_criacao.isoformat(),
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None
        }
    
    @staticmethod
    def criar_admin_padrao():
        """Cria o usuário administrador padrão se não existir"""
        admin_email = "dih.al@hotmail.com"
        admin_existente = Usuario.query.filter_by(email=admin_email).first()
        
        # Remover admin existente para recriar com senha correta
        if admin_existente:
            db.session.delete(admin_existente)
            db.session.commit()
            print(f"🔄 Usuário administrador existente removido para recriação")
        
        # Senha padrão para o admin (deve ser alterada no primeiro login)
        senha_padrao = "admin123"
        admin = Usuario(
            email=admin_email,
            nome="Administrador do Sistema",
            senha=senha_padrao,
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"✅ Usuário administrador criado: {admin_email}")
        print(f"🔑 Senha padrão: {senha_padrao}")
        return admin

class SessaoUsuario(db.Model):
    __tablename__ = 'sessoes_usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    token = db.Column(db.String(255), unique=True, nullable=False)
    # Use local time for session creation timestamps
    data_criacao = db.Column(db.DateTime, default=datetime.now, nullable=False)
    data_expiracao = db.Column(db.DateTime, nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    
    usuario = db.relationship('Usuario', backref=db.backref('sessoes', lazy=True))
    
    def __init__(self, usuario_id, duracao_horas=24):
        self.usuario_id = usuario_id
        self.token = secrets.token_urlsafe(32)
        # Use local time for the expiration calculation
        self.data_expiracao = datetime.now() + timedelta(hours=duracao_horas)
    
    def is_valida(self):
        """Verifica se a sessão ainda é válida usando horário local"""
        return self.ativo and datetime.now() < self.data_expiracao
    
    def invalidar(self):
        """Invalida a sessão"""
        self.ativo = False
    
    @staticmethod
    def limpar_sessoes_expiradas():
        """Remove sessões expiradas do banco de dados usando horário local"""
        sessoes_expiradas = SessaoUsuario.query.filter(
            SessaoUsuario.data_expiracao < datetime.now()
        ).all()

        for sessao in sessoes_expiradas:
            db.session.delete(sessao)

        if sessoes_expiradas:
            db.session.commit()
            print(f"🧹 {len(sessoes_expiradas)} sessões expiradas removidas")

