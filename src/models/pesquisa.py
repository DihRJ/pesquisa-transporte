from src.database import db
from datetime import datetime

class Pesquisa(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    linha_numero = db.Column(db.String(50), nullable=False)
    linha_itinerario = db.Column(db.String(200), nullable=True)
    pontualidade = db.Column(db.Integer, nullable=False)  # 1-10
    frequencia = db.Column(db.Integer, nullable=False)    # 1-10
    conforto = db.Column(db.Integer, nullable=False)      # 1-10
    atendimento = db.Column(db.Integer, nullable=False)   # 1-10
    infraestrutura = db.Column(db.Integer, nullable=False) # 1-10
    observacoes = db.Column(db.Text, nullable=True)
    # Use the local server time (respecting the TZ environment variable) instead of UTC.
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Pesquisa {self.linha_numero} - {self.data_criacao}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'linha_numero': self.linha_numero,
            'linha_itinerario': self.linha_itinerario,
            'pontualidade': self.pontualidade,
            'frequencia': self.frequencia,
            'conforto': self.conforto,
            'atendimento': self.atendimento,
            'infraestrutura': self.infraestrutura,
            'observacoes': self.observacoes,
            'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
        }
    
    def calcular_media(self):
        """Calcula a média das 5 perguntas"""
        return (self.pontualidade + self.frequencia + self.conforto + 
                self.atendimento + self.infraestrutura) / 5

class ContadorLinha(db.Model):
    """Modelo para controlar quantas pesquisas foram feitas por linha"""
    id = db.Column(db.Integer, primary_key=True)
    linha_numero = db.Column(db.String(50), unique=True, nullable=False)
    contador = db.Column(db.Integer, default=0)
    ultimo_envio = db.Column(db.DateTime, nullable=True)
    
    def __repr__(self):
        return f'<ContadorLinha {self.linha_numero}: {self.contador}>'

