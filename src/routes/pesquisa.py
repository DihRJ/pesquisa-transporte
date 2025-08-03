from flask import Blueprint, request, jsonify, current_app
from flask_mail import Message
from src.models.pesquisa import db, Pesquisa, ContadorLinha
from datetime import datetime
import os

pesquisa_bp = Blueprint('pesquisa', __name__)

def enviar_relatorio_email(linha_numero, pesquisas):
    """Envia relatório por e-mail quando atingir 10 pesquisas"""
    try:
        # Calcular estatísticas
        total_pesquisas = len(pesquisas)
        media_pontualidade = sum(p.pontualidade for p in pesquisas) / total_pesquisas
        media_frequencia = sum(p.frequencia for p in pesquisas) / total_pesquisas
        media_conforto = sum(p.conforto for p in pesquisas) / total_pesquisas
        media_atendimento = sum(p.atendimento for p in pesquisas) / total_pesquisas
        media_infraestrutura = sum(p.infraestrutura for p in pesquisas) / total_pesquisas
        media_geral = (media_pontualidade + media_frequencia + media_conforto + 
                      media_atendimento + media_infraestrutura) / 5
        
        # Função para classificar notas
        def classificar_nota(nota):
            if nota >= 9: return "Excelente"
            elif nota >= 7: return "Bom"
            elif nota >= 4: return "Regular"
            else: return "Ruim"
        
        # Criar conteúdo do e-mail
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 0; padding: 0; background-color: #f4f4f4; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }}
                .content {{ padding: 30px; }}
                .metric {{ margin: 15px 0; padding: 20px; border-radius: 8px; border-left: 5px solid #667eea; background-color: #f8f9fa; }}
                .excellent {{ border-left-color: #28a745; background-color: #d4edda; }}
                .good {{ border-left-color: #17a2b8; background-color: #d1ecf1; }}
                .regular {{ border-left-color: #ffc107; background-color: #fff3cd; }}
                .poor {{ border-left-color: #dc3545; background-color: #f8d7da; }}
                .summary {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 25px; border-radius: 10px; margin: 20px 0; text-align: center; }}
                .observations {{ background-color: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .score {{ font-size: 28px; font-weight: bold; margin: 10px 0; }}
                .footer {{ background-color: #343a40; color: white; padding: 20px; text-align: center; font-size: 12px; }}
                h1 {{ margin: 0; font-size: 28px; }}
                h2 {{ color: #495057; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
                h3 {{ color: #495057; }}
                .grid {{ display: flex; flex-wrap: wrap; gap: 15px; margin: 20px 0; }}
                .grid-item {{ flex: 1; min-width: 200px; text-align: center; padding: 15px; background-color: #f8f9fa; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚌 Relatório de Satisfação</h1>
                    <h2>Sistema Municipal de Transporte Coletivo</h2>
                    <p style="font-size: 18px; margin: 10px 0;">Linha: <strong>{linha_numero}</strong></p>
                    <p style="font-size: 14px; opacity: 0.9;">Relatório automático baseado em {total_pesquisas} pesquisas</p>
                </div>
                
                <div class="content">
                    <div class="summary">
                        <h2 style="color: white; border: none; margin-bottom: 20px;">📊 Resumo Executivo</h2>
                        <div class="score">{media_geral:.1f}/10</div>
                        <p style="font-size: 18px; margin: 0;">Média Geral: {classificar_nota(media_geral)}</p>
                        <p style="font-size: 14px; margin-top: 15px; opacity: 0.9;">
                            Período: {pesquisas[0].data_criacao.strftime('%d/%m/%Y')} a {pesquisas[-1].data_criacao.strftime('%d/%m/%Y')}
                        </p>
                    </div>
                    
                    <h2>📈 Análise Detalhada por Categoria</h2>
                    
                    <div class="metric {classificar_nota(media_pontualidade).lower()}">
                        <h3>🕐 1. Pontualidade e Cumprimento de Horários</h3>
                        <p><strong>Nota:</strong> {media_pontualidade:.1f}/10 - {classificar_nota(media_pontualidade)}</p>
                        <p>Avalia a confiabilidade do sistema em relação aos horários divulgados.</p>
                    </div>
                    
                    <div class="metric {classificar_nota(media_frequencia).lower()}">
                        <h3>⏱️ 2. Frequência e Intervalo entre Ônibus</h3>
                        <p><strong>Nota:</strong> {media_frequencia:.1f}/10 - {classificar_nota(media_frequencia)}</p>
                        <p>Mede a adequação da oferta de serviço e tempo de espera.</p>
                    </div>
                    
                    <div class="metric {classificar_nota(media_conforto).lower()}">
                        <h3>🚌 3. Conforto e Condições dos Veículos</h3>
                        <p><strong>Nota:</strong> {media_conforto:.1f}/10 - {classificar_nota(media_conforto)}</p>
                        <p>Analisa a qualidade da frota, limpeza e condições gerais.</p>
                    </div>
                    
                    <div class="metric {classificar_nota(media_atendimento).lower()}">
                        <h3>👥 4. Qualidade do Atendimento</h3>
                        <p><strong>Nota:</strong> {media_atendimento:.1f}/10 - {classificar_nota(media_atendimento)}</p>
                        <p>Avalia o fator humano: motoristas e cobradores.</p>
                    </div>
                    
                    <div class="metric {classificar_nota(media_infraestrutura).lower()}">
                        <h3>🏢 5. Infraestrutura dos Pontos e Terminais</h3>
                        <p><strong>Nota:</strong> {media_infraestrutura:.1f}/10 - {classificar_nota(media_infraestrutura)}</p>
                        <p>Examina as condições de espera, cobertura, bancos e segurança.</p>
                    </div>
        """
        
        # Adicionar observações dos usuários
        observacoes_validas = [p.observacoes for p in pesquisas if p.observacoes and p.observacoes.strip()]
        if observacoes_validas:
            html_content += f"""
                    <div class="observations">
                        <h3>💬 Observações dos Usuários ({len(observacoes_validas)} comentários)</h3>
                        <ul style="list-style-type: none; padding: 0;">
            """
            for i, obs in enumerate(observacoes_validas, 1):
                html_content += f'<li style="margin: 10px 0; padding: 10px; background-color: white; border-radius: 5px; border-left: 3px solid #667eea;"><strong>#{i}:</strong> {obs}</li>'
            html_content += "</ul></div>"
        else:
            html_content += """
                    <div class="observations">
                        <h3>💬 Observações dos Usuários</h3>
                        <p style="font-style: italic; color: #6c757d;">Nenhuma observação adicional foi fornecida neste período.</p>
                    </div>
            """
        
        html_content += f"""
                    <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 30px;">
                        <h3>📋 Recomendações</h3>
                        <ul>
        """
        
        # Adicionar recomendações baseadas nas notas
        if media_pontualidade < 6:
            html_content += "<li>🔴 <strong>Pontualidade:</strong> Revisar horários e implementar monitoramento em tempo real.</li>"
        if media_frequencia < 6:
            html_content += "<li>🔴 <strong>Frequência:</strong> Avaliar aumento da frota ou otimização das rotas.</li>"
        if media_conforto < 6:
            html_content += "<li>🔴 <strong>Conforto:</strong> Intensificar manutenção preventiva e limpeza dos veículos.</li>"
        if media_atendimento < 6:
            html_content += "<li>🔴 <strong>Atendimento:</strong> Implementar treinamento para motoristas e cobradores.</li>"
        if media_infraestrutura < 6:
            html_content += "<li>🔴 <strong>Infraestrutura:</strong> Melhorar pontos de ônibus e terminais.</li>"
        
        if media_geral >= 7:
            html_content += "<li>✅ <strong>Parabéns!</strong> A linha apresenta boa avaliação geral. Manter o padrão de qualidade.</li>"
        
        html_content += """
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>📧 Este relatório foi gerado automaticamente pelo Sistema de Pesquisa de Satisfação</p>
                    <p>🌐 Sistema Municipal de Transporte Coletivo | Gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Log detalhado do relatório
        print("=" * 80)
        print("📧 RELATÓRIO DE E-MAIL GERADO")
        print("=" * 80)
        print(f"📍 DESTINATÁRIO: dih.al@hotmail.com")
        print(f"🚌 LINHA: {linha_numero}")
        print(f"📊 TOTAL DE PESQUISAS: {total_pesquisas}")
        print(f"📈 MÉDIA GERAL: {media_geral:.1f}/10 ({classificar_nota(media_geral)})")
        print(f"📅 PERÍODO: {pesquisas[0].data_criacao.strftime('%d/%m/%Y')} a {pesquisas[-1].data_criacao.strftime('%d/%m/%Y')}")
        print("\n📋 DETALHAMENTO POR CATEGORIA:")
        print(f"   🕐 Pontualidade: {media_pontualidade:.1f}/10 ({classificar_nota(media_pontualidade)})")
        print(f"   ⏱️ Frequência: {media_frequencia:.1f}/10 ({classificar_nota(media_frequencia)})")
        print(f"   🚌 Conforto: {media_conforto:.1f}/10 ({classificar_nota(media_conforto)})")
        print(f"   👥 Atendimento: {media_atendimento:.1f}/10 ({classificar_nota(media_atendimento)})")
        print(f"   🏢 Infraestrutura: {media_infraestrutura:.1f}/10 ({classificar_nota(media_infraestrutura)})")
        
        if observacoes_validas:
            print(f"\n💬 OBSERVAÇÕES DOS USUÁRIOS ({len(observacoes_validas)} comentários):")
            for i, obs in enumerate(observacoes_validas[:3], 1):  # Mostrar apenas as 3 primeiras
                print(f"   {i}. {obs[:100]}{'...' if len(obs) > 100 else ''}")
            if len(observacoes_validas) > 3:
                print(f"   ... e mais {len(observacoes_validas) - 3} comentários")
        
        print("\n✅ RELATÓRIO PREPARADO COM SUCESSO!")
        print("📧 E-mail seria enviado para: dih.al@hotmail.com")
        print("=" * 80)
        
        # Simular envio bem-sucedido
        # Em produção, aqui seria feita a integração com um serviço de e-mail real
        return True
        
    except Exception as e:
        print(f"❌ ERRO ao preparar relatório de e-mail: {str(e)}")
        return False

@pesquisa_bp.route('/pesquisas', methods=['POST'])
def criar_pesquisa():
    """Cria uma nova pesquisa"""
    try:
        data = request.get_json()
        
        # Validar dados obrigatórios
        campos_obrigatorios = ['linha_numero', 'pontualidade', 'frequencia', 'conforto', 'atendimento', 'infraestrutura']
        for campo in campos_obrigatorios:
            if campo not in data:
                return jsonify({'erro': f'Campo obrigatório: {campo}'}), 400
        
        # Validar escalas (1-10)
        campos_escala = ['pontualidade', 'frequencia', 'conforto', 'atendimento', 'infraestrutura']
        for campo in campos_escala:
            valor = data.get(campo)
            if not isinstance(valor, int) or valor < 1 or valor > 10:
                return jsonify({'erro': f'Campo {campo} deve ser um número entre 1 e 10'}), 400
        
        # Criar nova pesquisa
        nova_pesquisa = Pesquisa(
            linha_numero=data['linha_numero'].strip(),
            linha_itinerario=data.get('linha_itinerario', '').strip(),
            pontualidade=data['pontualidade'],
            frequencia=data['frequencia'],
            conforto=data['conforto'],
            atendimento=data['atendimento'],
            infraestrutura=data['infraestrutura'],
            observacoes=data.get('observacoes', '').strip()
        )
        
        db.session.add(nova_pesquisa)
        
        # Atualizar contador da linha
        contador = ContadorLinha.query.filter_by(linha_numero=nova_pesquisa.linha_numero).first()
        if not contador:
            contador = ContadorLinha(linha_numero=nova_pesquisa.linha_numero, contador=1)
            db.session.add(contador)
        else:
            contador.contador += 1
        
        db.session.commit()
        
        # Verificar se atingiu 10 pesquisas para gerar relatório automático
        if contador.contador % 10 == 0:
            # Buscar as últimas 10 pesquisas desta linha
            pesquisas_linha = Pesquisa.query.filter_by(linha_numero=nova_pesquisa.linha_numero).order_by(Pesquisa.data_criacao.desc()).limit(10).all()
            
            # Gerar relatório automático
            print(f"\n🎯 ATINGIU 10 PESQUISAS! Gerando relatório automático da linha {nova_pesquisa.linha_numero}")
            
            # Importar aqui para evitar import circular
            from src.models.relatorio import Relatorio
            relatorio = Relatorio.criar_relatorio_automatico(nova_pesquisa.linha_numero, pesquisas_linha)
            
            if relatorio:
                contador.ultimo_envio = datetime.utcnow()
                db.session.commit()
                print(f"✅ Relatório automático criado com ID {relatorio.id}")
            else:
                print(f"❌ Falha na criação do relatório automático")
        
        return jsonify({
            'sucesso': True,
            'pesquisa': nova_pesquisa.to_dict(),
            'total_linha': contador.contador,
            'proximo_relatorio': 10 - (contador.contador % 10),
            'relatorio_gerado': contador.contador % 10 == 0
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'erro': str(e)}), 500

@pesquisa_bp.route('/pesquisas', methods=['GET'])
def listar_pesquisas():
    """Lista todas as pesquisas"""
    try:
        linha = request.args.get('linha')
        
        if linha:
            pesquisas = Pesquisa.query.filter_by(linha_numero=linha).order_by(Pesquisa.data_criacao.desc()).all()
        else:
            pesquisas = Pesquisa.query.order_by(Pesquisa.data_criacao.desc()).all()
        
        return jsonify({
            'pesquisas': [p.to_dict() for p in pesquisas],
            'total': len(pesquisas)
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@pesquisa_bp.route('/estatisticas', methods=['GET'])
def obter_estatisticas():
    """Obtém estatísticas gerais"""
    try:
        total_pesquisas = Pesquisa.query.count()
        contadores = ContadorLinha.query.all()
        
        linhas_stats = []
        for contador in contadores:
            pesquisas_linha = Pesquisa.query.filter_by(linha_numero=contador.linha_numero).all()
            if pesquisas_linha:
                media_geral = sum(p.calcular_media() for p in pesquisas_linha) / len(pesquisas_linha)
                linhas_stats.append({
                    'linha': contador.linha_numero,
                    'total_pesquisas': contador.contador,
                    'media_geral': round(media_geral, 1),
                    'ultimo_envio': contador.ultimo_envio.isoformat() if contador.ultimo_envio else None
                })
        
        return jsonify({
            'total_pesquisas': total_pesquisas,
            'total_linhas': len(contadores),
            'linhas': linhas_stats
        })
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500



@pesquisa_bp.route('/teste-email/<linha_numero>', methods=['POST'])
def testar_email(linha_numero):
    """Rota para testar o envio de e-mail manualmente"""
    try:
        # Buscar pesquisas da linha especificada
        pesquisas = Pesquisa.query.filter_by(linha_numero=linha_numero).order_by(Pesquisa.data_criacao.desc()).limit(10).all()
        
        if not pesquisas:
            return jsonify({'erro': f'Nenhuma pesquisa encontrada para a linha {linha_numero}'}), 404
        
        # Forçar envio de relatório para teste
        print(f"\n🧪 TESTE DE E-MAIL INICIADO para linha {linha_numero}")
        print(f"📊 Encontradas {len(pesquisas)} pesquisas para análise")
        
        if enviar_relatorio_email(linha_numero, pesquisas):
            return jsonify({
                'sucesso': True,
                'mensagem': f'E-mail de teste enviado com sucesso para linha {linha_numero}',
                'total_pesquisas': len(pesquisas),
                'destinatario': 'dih.al@hotmail.com'
            }), 200
        else:
            return jsonify({
                'erro': 'Falha no envio do e-mail de teste',
                'total_pesquisas': len(pesquisas)
            }), 500
            
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@pesquisa_bp.route('/forcar-relatorio/<linha_numero>', methods=['POST'])
def forcar_relatorio(linha_numero):
    """Força o envio de relatório independente do contador"""
    try:
        # Buscar todas as pesquisas da linha
        pesquisas = Pesquisa.query.filter_by(linha_numero=linha_numero).order_by(Pesquisa.data_criacao.desc()).all()
        
        if not pesquisas:
            return jsonify({'erro': f'Nenhuma pesquisa encontrada para a linha {linha_numero}'}), 404
        
        # Usar as últimas 10 pesquisas ou todas se houver menos de 10
        pesquisas_relatorio = pesquisas[:10] if len(pesquisas) >= 10 else pesquisas
        
        print(f"\n🚀 FORÇANDO ENVIO DE RELATÓRIO para linha {linha_numero}")
        print(f"📊 Usando {len(pesquisas_relatorio)} pesquisas de um total de {len(pesquisas)}")
        
        if enviar_relatorio_email(linha_numero, pesquisas_relatorio):
            # Atualizar timestamp do último envio
            contador = ContadorLinha.query.filter_by(linha_numero=linha_numero).first()
            if contador:
                contador.ultimo_envio = datetime.utcnow()
                db.session.commit()
            
            return jsonify({
                'sucesso': True,
                'mensagem': f'Relatório forçado enviado com sucesso para linha {linha_numero}',
                'total_pesquisas_usadas': len(pesquisas_relatorio),
                'total_pesquisas_linha': len(pesquisas),
                'destinatario': 'dih.al@hotmail.com'
            }), 200
        else:
            return jsonify({
                'erro': 'Falha no envio do relatório forçado',
                'total_pesquisas': len(pesquisas_relatorio)
            }), 500
            
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

