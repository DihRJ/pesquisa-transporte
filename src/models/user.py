from flask_sqlalchemy import SQLAlchemy

# Instância do SQLAlchemy para este modelo

# NOTE: Aqui instanciamos um novo SQLAlchemy apenas se necessário, porém no projeto usamos uma única instância compartilhada
# via src.database import db. Este arquivo original define uma nova instância, mas isso é apenas para referencia.
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email
        }
