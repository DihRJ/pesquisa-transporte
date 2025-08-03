from flask import Blueprint, request, jsonify, send_file
from src.database import db
from src.models.relatorio import Relatorio
from src.models.pesquisa import Pesquisa
from src.routes.auth import requer_login
from src.utils.geradores_simples import gerar_excel_simples, gerar_pdf_simples, gerar_word_simples
from datetime import datetime
import io
import json
import csv
import tempfile
import os

relatorios_bp = Blueprint('relatorios', __name__)

@relatorios_bp.route('/relatorios', methods=['GET'])
@requer_login
def listar_relatorios(usuario_atual):
    """Lista todos os relatórios disponíveis"""
    try:
        # Parâmetros de filtro
        linha = request.args.get('linha')
        limite = request.args.get('limite', 50, type=int)
        pagina = request.args.get('pagina', 1, type=int)
        
        # Query base
        query = Relatorio.query
        
        # Filtrar por linha se especificado
        if linha:
            query = query.filter(Relatorio.linha_numero.ilike(f'%{linha}%'))
        
        # Ordenar por data de criação (mais recentes primeiro)
        query = query.order_by(Relatorio.data_criacao.desc())
        
        # Paginação
        offset = (pagina - 1) * limite
        relatorios = query.offset(offset).limit(limite).all()
        total = query.count()
        
        return jsonify({
            'relatorios': [r.to_dict() for r in relatorios],
            'total': total,
            'pagina': pagina,
            'limite': limite,
            'total_paginas': (total + limite - 1) // limite
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@relatorios_bp.route('/relatorios/<int:relatorio_id>', methods=['GET'])
@requer_login
def obter_relatorio(usuario_atual, relatorio_id):
    """Obtém detalhes completos de um relatório"""
    try:
        relatorio = Relatorio.query.get_or_404(relatorio_id)
        
        dados_completos = relatorio.to_dict()
        dados_completos['pesquisas'] = relatorio.get_dados_pesquisas()
        dados_completos['observacoes_lista'] = relatorio.get_observacoes_lista()
        
        return jsonify(dados_completos), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@relatorios_bp.route('/relatorios/estatisticas', methods=['GET'])
@requer_login
def obter_estatisticas_relatorios(usuario_atual):
    """Obtém estatísticas gerais dos relatórios"""
    try:
        total_relatorios = Relatorio.query.count()
        
        # Relatórios por linha
        relatorios_por_linha = db.session.query(
            Relatorio.linha_numero,
            db.func.count(Relatorio.id).label('total'),
            db.func.avg(Relatorio.media_geral).label('media_geral'),
            db.func.max(Relatorio.data_criacao).label('ultimo_relatorio')
        ).group_by(Relatorio.linha_numero).all()
        
        linhas_stats = []
        for linha, total, media, ultimo in relatorios_por_linha:
            linhas_stats.append({
                'linha': linha,
                'total_relatorios': total,
                'media_geral': round(media, 1) if media else 0,
                'ultimo_relatorio': ultimo.isoformat() if ultimo else None
            })
        
        # Ordenar por média geral (pior primeiro para destacar problemas)
        linhas_stats.sort(key=lambda x: x['media_geral'])
        
        return jsonify({
            'total_relatorios': total_relatorios,
            'total_linhas': len(linhas_stats),
            'linhas': linhas_stats
        }), 200
        
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

@relatorios_bp.route('/relatorios/<int:relatorio_id>/download/<formato>', methods=['GET'])
@requer_login
def download_relatorio(usuario_atual, relatorio_id, formato):
    """Faz download do relatório em diferentes formatos"""
    try:
        relatorio = Relatorio.query.get_or_404(relatorio_id)
        
        if formato.lower() == 'json':
            return download_json(relatorio)
        elif formato.lower() == 'csv':
            return download_csv(relatorio)
        elif formato.lower() == 'pdf':
            return download_pdf_simples(relatorio)
        elif formato.lower() == 'excel' or formato.lower() == 'xlsx':
            return download_excel_simples(relatorio)
        elif formato.lower() == 'word' or formato.lower() == 'docx':
            return download_word_simples(relatorio)
        elif formato.lower() == 'html':
            return download_html(relatorio)
        else:
            return jsonify({'erro': 'Formato não suportado. Use: json, csv, pdf, excel, word, html'}), 400
            
    except Exception as e:
        return jsonify({'erro': str(e)}), 500

def download_json(relatorio):
    """Gera download em formato JSON"""
    dados = relatorio.to_dict()
    dados['pesquisas'] = relatorio.get_dados_pesquisas()
    dados['observacoes_lista'] = relatorio.get_observacoes_lista()
    
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)
        temp_path = f.name
    
    filename = f"relatorio_linha_{relatorio.linha_numero}_{relatorio.data_criacao.strftime('%Y%m%d_%H%M%S')}.json"
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='application/json'
    )

def download_csv(relatorio):
    """Gera download em formato CSV"""
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        
        # Cabeçalho do relatório
        writer.writerow(['RELATÓRIO DE SATISFAÇÃO - TRANSPORTE MUNICIPAL'])
        writer.writerow([f'Linha: {relatorio.linha_numero}'])
        writer.writerow([f'Período: {relatorio.periodo_inicio.strftime("%d/%m/%Y")} a {relatorio.periodo_fim.strftime("%d/%m/%Y")}'])
        writer.writerow([f'Total de Pesquisas: {relatorio.total_pesquisas}'])
        writer.writerow([f'Gerado em: {relatorio.data_criacao.strftime("%d/%m/%Y às %H:%M")}'])
        writer.writerow([])
        
        # Médias por categoria
        writer.writerow(['MÉDIAS POR CATEGORIA'])
        writer.writerow(['Categoria', 'Média', 'Classificação'])
        writer.writerow(['Pontualidade', f'{relatorio.media_pontualidade:.1f}', relatorio.classificar_nota(relatorio.media_pontualidade)])
        writer.writerow(['Frequência', f'{relatorio.media_frequencia:.1f}', relatorio.classificar_nota(relatorio.media_frequencia)])
        writer.writerow(['Conforto', f'{relatorio.media_conforto:.1f}', relatorio.classificar_nota(relatorio.media_conforto)])
        writer.writerow(['Atendimento', f'{relatorio.media_atendimento:.1f}', relatorio.classificar_nota(relatorio.media_atendimento)])
        writer.writerow(['Infraestrutura', f'{relatorio.media_infraestrutura:.1f}', relatorio.classificar_nota(relatorio.media_infraestrutura)])
        writer.writerow(['MÉDIA GERAL', f'{relatorio.media_geral:.1f}', relatorio.get_classificacao_geral()])
        writer.writerow([])
        
        # Dados detalhados das pesquisas
        writer.writerow(['DADOS DETALHADOS DAS PESQUISAS'])
        writer.writerow(['ID', 'Data', 'Itinerário', 'Pontualidade', 'Frequência', 'Conforto', 'Atendimento', 'Infraestrutura', 'Observações'])
        
        pesquisas = relatorio.get_dados_pesquisas()
        for p in pesquisas:
            writer.writerow([
                p['id'],
                datetime.fromisoformat(p['data_criacao']).strftime('%d/%m/%Y %H:%M'),
                p['linha_itinerario'] or '',
                p['pontualidade'],
                p['frequencia'],
                p['conforto'],
                p['atendimento'],
                p['infraestrutura'],
                p['observacoes'] or ''
            ])
        
        # Recomendações
        writer.writerow([])
        writer.writerow(['RECOMENDAÇÕES'])
        for rec in relatorio.get_recomendacoes():
            writer.writerow([rec])
        
        temp_path = f.name
    
    filename = f"relatorio_linha_{relatorio.linha_numero}_{relatorio.data_criacao.strftime('%Y%m%d_%H%M%S')}.csv"
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )

def download_html(relatorio):
    """Gera download em formato HTML"""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de Satisfação - Linha {relatorio.linha_numero}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }}
            .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px; margin-bottom: 30px; }}
            .metric {{ margin: 15px 0; padding: 20px; border-radius: 8px; border-left: 5px solid #667eea; background-color: #f8f9fa; }}
            .excellent {{ border-left-color: #28a745; background-color: #d4edda; }}
            .good {{ border-left-color: #17a2b8; background-color: #d1ecf1; }}
            .regular {{ border-left-color: #ffc107; background-color: #fff3cd; }}
            .poor {{ border-left-color: #dc3545; background-color: #f8d7da; }}
            .summary {{ background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 25px; border-radius: 10px; margin: 20px 0; text-align: center; }}
            .observations {{ background-color: #e9ecef; padding: 20px; border-radius: 8px; margin: 20px 0; }}
            .score {{ font-size: 28px; font-weight: bold; margin: 10px 0; }}
            h1 {{ margin: 0; font-size: 28px; }}
            h2 {{ color: #495057; border-bottom: 2px solid #667eea; padding-bottom: 10px; }}
            h3 {{ color: #495057; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f8f9fa; font-weight: bold; }}
            .print-only {{ display: none; }}
            @media print {{
                .print-only {{ display: block; }}
                body {{ background-color: white; }}
                .container {{ box-shadow: none; }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚌 Relatório de Satisfação</h1>
                <h2>Sistema Municipal de Transporte Coletivo</h2>
                <p style="font-size: 18px; margin: 10px 0;">Linha: <strong>{relatorio.linha_numero}</strong></p>
                <p style="font-size: 14px; opacity: 0.9;">Relatório baseado em {relatorio.total_pesquisas} pesquisas</p>
            </div>
            
            <div class="summary">
                <h2 style="color: white; border: none; margin-bottom: 20px;">📊 Resumo Executivo</h2>
                <div class="score">{relatorio.media_geral:.1f}/10</div>
                <p style="font-size: 18px; margin: 0;">Média Geral: {relatorio.get_classificacao_geral()}</p>
                <p style="font-size: 14px; margin-top: 15px; opacity: 0.9;">
                    Período: {relatorio.periodo_inicio.strftime('%d/%m/%Y')} a {relatorio.periodo_fim.strftime('%d/%m/%Y')}
                </p>
            </div>
            
            <h2>📈 Análise Detalhada por Categoria</h2>
            
            <div class="metric {relatorio.classificar_nota(relatorio.media_pontualidade).lower()}">
                <h3>🕐 1. Pontualidade e Cumprimento de Horários</h3>
                <p><strong>Nota:</strong> {relatorio.media_pontualidade:.1f}/10 - {relatorio.classificar_nota(relatorio.media_pontualidade)}</p>
                <p>Avalia a confiabilidade do sistema em relação aos horários divulgados.</p>
            </div>
            
            <div class="metric {relatorio.classificar_nota(relatorio.media_frequencia).lower()}">
                <h3>⏱️ 2. Frequência e Intervalo entre Ônibus</h3>
                <p><strong>Nota:</strong> {relatorio.media_frequencia:.1f}/10 - {relatorio.classificar_nota(relatorio.media_frequencia)}</p>
                <p>Mede a adequação da oferta de serviço e tempo de espera.</p>
            </div>
            
            <div class="metric {relatorio.classificar_nota(relatorio.media_conforto).lower()}">
                <h3>🚌 3. Conforto e Condições dos Veículos</h3>
                <p><strong>Nota:</strong> {relatorio.media_conforto:.1f}/10 - {relatorio.classificar_nota(relatorio.media_conforto)}</p>
                <p>Analisa a qualidade da frota, limpeza e condições gerais.</p>
            </div>
            
            <div class="metric {relatorio.classificar_nota(relatorio.media_atendimento).lower()}">
                <h3>👥 4. Qualidade do Atendimento</h3>
                <p><strong>Nota:</strong> {relatorio.media_atendimento:.1f}/10 - {relatorio.classificar_nota(relatorio.media_atendimento)}</p>
                <p>Avalia o fator humano: motoristas e cobradores.</p>
            </div>
            
            <div class="metric {relatorio.classificar_nota(relatorio.media_infraestrutura).lower()}">
                <h3>🏢 5. Infraestrutura dos Pontos e Terminais</h3>
                <p><strong>Nota:</strong> {relatorio.media_infraestrutura:.1f}/10 - {relatorio.classificar_nota(relatorio.media_infraestrutura)}</p>
                <p>Examina as condições de espera, cobertura, bancos e segurança.</p>
            </div>
    """
    
    # Adicionar observações dos usuários
    observacoes = relatorio.get_observacoes_lista()
    if observacoes:
        html_content += f"""
            <div class="observations">
                <h3>💬 Observações dos Usuários ({len(observacoes)} comentários)</h3>
                <ul style="list-style-type: none; padding: 0;">
        """
        for i, obs in enumerate(observacoes, 1):
            html_content += f'<li style="margin: 10px 0; padding: 10px; background-color: white; border-radius: 5px; border-left: 3px solid #667eea;"><strong>#{i}:</strong> {obs}</li>'
        html_content += "</ul></div>"
    else:
        html_content += """
            <div class="observations">
                <h3>💬 Observações dos Usuários</h3>
                <p style="font-style: italic; color: #6c757d;">Nenhuma observação adicional foi fornecida neste período.</p>
            </div>
        """
    
    # Adicionar recomendações
    recomendacoes = relatorio.get_recomendacoes()
    html_content += f"""
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-top: 30px;">
                <h3>📋 Recomendações</h3>
                <ul>
    """
    for rec in recomendacoes:
        html_content += f"<li>{rec}</li>"
    
    html_content += f"""
                </ul>
            </div>
            
            <div class="print-only" style="margin-top: 30px; text-align: center; font-size: 12px; color: #666;">
                <p>📧 Relatório gerado automaticamente pelo Sistema de Pesquisa de Satisfação</p>
                <p>🌐 Sistema Municipal de Transporte Coletivo | Gerado em {relatorio.data_criacao.strftime('%d/%m/%Y às %H:%M')}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        temp_path = f.name
    
    filename = f"relatorio_linha_{relatorio.linha_numero}_{relatorio.data_criacao.strftime('%Y%m%d_%H%M%S')}.html"
    
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=filename,
        mimetype='text/html'
    )

def download_pdf(relatorio):
    """Gera download em formato PDF (placeholder - requer biblioteca adicional)"""
    # Para implementar PDF, seria necessário instalar weasyprint ou reportlab
    # Por enquanto, retorna HTML que pode ser convertido para PDF pelo navegador
    return download_html(relatorio)


def download_pdf_simples(relatorio):
    """Gera download em formato HTML (pode ser convertido para PDF)"""
    try:
        temp_path = gerar_pdf_simples(relatorio)
        filename = f"relatorio_linha_{relatorio.linha_numero}_{relatorio.data_criacao.strftime('%Y%m%d_%H%M%S')}.html"
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )
    except Exception as e:
        return jsonify({'erro': f'Erro ao gerar PDF: {str(e)}'}), 500

def download_excel_simples(relatorio):
    """Gera download em formato CSV (compatível com Excel)"""
    try:
        temp_path = gerar_excel_simples(relatorio)
        filename = f"relatorio_linha_{relatorio.linha_numero}_{relatorio.data_criacao.strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/csv'
        )
    except Exception as e:
        return jsonify({'erro': f'Erro ao gerar Excel: {str(e)}'}), 500

def download_word_simples(relatorio):
    """Gera download em formato HTML (pode ser convertido para Word)"""
    try:
        temp_path = gerar_word_simples(relatorio)
        filename = f"relatorio_linha_{relatorio.linha_numero}_{relatorio.data_criacao.strftime('%Y%m%d_%H%M%S')}.html"
        
        return send_file(
            temp_path,
            as_attachment=True,
            download_name=filename,
            mimetype='text/html'
        )
    except Exception as e:
        return jsonify({'erro': f'Erro ao gerar documento Word: {str(e)}'}), 500

