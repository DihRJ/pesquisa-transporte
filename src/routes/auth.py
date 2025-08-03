from flask import Blueprint, request, jsonify, session
from src.database import db
from src.models.usuario import Usuario, SessaoUsuario
from datetime import datetime, timedelta
import secrets

auth_bp = Blueprint('auth', __name__)

def verificar_sessao():
    """Verifica se o usuário está logado"""
    token = request.headers.get('Authorization')
    if not token:
        token = session.get('token_usuario')
    
    if not token:
        return None
    
    # Remove 'Bearer ' se presente
    if token.startswith('Bearer '):
        token = token[7:]
    
    usuario = Usuario.query.filter_by(token_sessao=token, ativo=True).first()
    return usuario

def requer_login(f):
    """Decorator para rotas que requerem login"""
    def decorated_function(*args, **kwargs):
        usuario = verificar_sessao()
        if not usuario:
            return jsonify({'erro': 'Login necessário'}), 401
        return f(usuario, *args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

def requer_admin(f):
    """Decorator para rotas que requerem privilégios de admin"""
    def decorated_function(*args, **kwargs):
        usuario = verificar_sessao()
        if not usuario:
            return jsonify({'erro': 'Login necessário'}), 401
        if not usuario.is_admin:
            return jsonify({'erro': 'Acesso negado. Privilégios de administrador necessários.'}), 403
        return f(usuario, *args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@auth_bp.route('/login', methods=['POST'])
def login():
    """Rota de login"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('senha'):
            return jsonify({'erro': 'Email e senha são obrigatórios'}), 400
        
        email = data['email'].lower().strip()
        senha = data['senha']
        
        # Buscar usuário
        usuario = Usuario.query.filter_by(email=email, ativo=True).first()
        
        if not usuario or not usuario.verificar_senha(senha):
            return jsonify({'erro': 'Email ou senha incorretos'}), 401
        
        # Fazer login
        usuario.fazer_login()
        db.session.commit()
        
        # Armazenar token na sessão
        session['token_usuario'] = usuario.token_sessao
        session['usuario_id'] = usuario.id
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Login realizado com sucesso',
            'usuario': usuario.to_dict(),
            'token': usuario.token_sessao
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@requer_login
def logout(usuario_atual):
    """Rota de logout"""
    try:
        # Invalidar token
        usuario_atual.token_sessao = secrets.token_urlsafe(32)
        db.session.commit()
        
        # Limpar sessão
        session.clear()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Logout realizado com sucesso'
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@auth_bp.route('/perfil', methods=['GET'])
@requer_login
def obter_perfil(usuario_atual):
    """Obtém o perfil do usuário logado"""
    return jsonify({
        'usuario': usuario_atual.to_dict()
    }), 200

@auth_bp.route('/alterar-senha', methods=['POST'])
@requer_login
def alterar_senha(usuario_atual):
    """Altera a senha do usuário"""
    try:
        data = request.get_json()
        
        if not data or not data.get('senha_atual') or not data.get('nova_senha'):
            return jsonify({'erro': 'Senha atual e nova senha são obrigatórias'}), 400
        
        # Verificar senha atual
        if not usuario_atual.verificar_senha(data['senha_atual']):
            return jsonify({'erro': 'Senha atual incorreta'}), 401
        
        # Validar nova senha
        nova_senha = data['nova_senha']
        if len(nova_senha) < 6:
            return jsonify({'erro': 'Nova senha deve ter pelo menos 6 caracteres'}), 400
        
        # Alterar senha
        usuario_atual.alterar_senha(nova_senha)
        db.session.commit()
        
        # Atualizar token na sessão
        session['token_usuario'] = usuario_atual.token_sessao
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Senha alterada com sucesso',
            'token': usuario_atual.token_sessao
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@auth_bp.route('/usuarios', methods=['GET'])
@requer_admin
def listar_usuarios(usuario_atual):
    """Lista todos os usuários (apenas admin)"""
    try:
        usuarios = Usuario.query.order_by(Usuario.data_criacao.desc()).all()
        
        return jsonify({
            'usuarios': [u.to_dict() for u in usuarios],
            'total': len(usuarios)
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@auth_bp.route('/usuarios', methods=['POST'])
@requer_admin
def criar_usuario(usuario_atual):
    """Cria um novo usuário (apenas admin)"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        campos_obrigatorios = ['email', 'nome', 'senha']
        for campo in campos_obrigatorios:
            if not data or not data.get(campo):
                return jsonify({'erro': f'Campo obrigatório: {campo}'}), 400
        
        email = data['email'].lower().strip()
        nome = data['nome'].strip()
        senha = data['senha']
        is_admin = data.get('is_admin', False)
        
        # Validações
        if len(senha) < 6:
            return jsonify({'erro': 'Senha deve ter pelo menos 6 caracteres'}), 400
        
        # Verificar se email já existe
        usuario_existente = Usuario.query.filter_by(email=email).first()
        if usuario_existente:
            return jsonify({'erro': 'Email já está em uso'}), 400
        
        # Criar usuário
        novo_usuario = Usuario(
            email=email,
            nome=nome,
            senha=senha,
            is_admin=is_admin
        )
        
        db.session.add(novo_usuario)
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Usuário criado com sucesso',
            'usuario': novo_usuario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@auth_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
@requer_admin
def atualizar_usuario(usuario_atual, usuario_id):
    """Atualiza um usuário (apenas admin)"""
    try:
        usuario = Usuario.query.get_or_404(usuario_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'erro': 'Dados não fornecidos'}), 400
        
        # Atualizar campos permitidos
        if 'nome' in data:
            usuario.nome = data['nome'].strip()
        
        if 'ativo' in data:
            usuario.ativo = bool(data['ativo'])
        
        if 'is_admin' in data:
            # Não permitir remover admin do próprio usuário
            if usuario.id == usuario_atual.id and not data['is_admin']:
                return jsonify({'erro': 'Não é possível remover privilégios de admin de si mesmo'}), 400
            usuario.is_admin = bool(data['is_admin'])
        
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Usuário atualizado com sucesso',
            'usuario': usuario.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@auth_bp.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
@requer_admin
def deletar_usuario(usuario_atual, usuario_id):
    """Deleta um usuário (apenas admin)"""
    try:
        if usuario_id == usuario_atual.id:
            return jsonify({'erro': 'Não é possível deletar a si mesmo'}), 400
        
        usuario = Usuario.query.get_or_404(usuario_id)
        
        # Desativar ao invés de deletar para manter integridade
        usuario.ativo = False
        db.session.commit()
        
        return jsonify({
            'sucesso': True,
            'mensagem': 'Usuário desativado com sucesso'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@auth_bp.route('/verificar-sessao', methods=['GET'])
def verificar_sessao_route():
    """Verifica se a sessão atual é válida"""
    usuario = verificar_sessao()
    
    if usuario:
        return jsonify({
            'logado': True,
            'usuario': usuario.to_dict()
        }), 200
    else:
        return jsonify({
            'logado': False
        }), 200
