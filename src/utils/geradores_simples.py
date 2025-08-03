import tempfile
import os
from datetime import datetime
import json
import csv

def gerar_excel_simples(relatorio):
    """Gera um arquivo CSV que pode ser aberto no Excel"""
    
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
        
        return f.name

def gerar_pdf_simples(relatorio):
    """Gera um arquivo HTML que pode ser convertido para PDF"""
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Relatório de Satisfação - Linha {relatorio.linha_numero}</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
            }}
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                text-align: center;
                border-bottom: 3px solid #4472C4;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            .title {{
                font-size: 24px;
                font-weight: bold;
                color: #4472C4;
                margin-bottom: 10px;
            }}
            .subtitle {{
                font-size: 16px;
                color: #666;
            }}
            .info-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .info-table th, .info-table td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            .info-table th {{
                background-color: #f8f9fa;
                font-weight: bold;
            }}
            .section-title {{
                font-size: 18px;
                font-weight: bold;
                color: #4472C4;
                margin: 30px 0 15px 0;
                border-bottom: 2px solid #4472C4;
                padding-bottom: 5px;
            }}
            .metric {{
                margin: 15px 0;
                padding: 15px;
                border-left: 5px solid #4472C4;
                background-color: #f8f9fa;
            }}
            .metric.excellent {{ border-left-color: #28a745; background-color: #d4edda; }}
            .metric.good {{ border-left-color: #17a2b8; background-color: #d1ecf1; }}
            .metric.regular {{ border-left-color: #ffc107; background-color: #fff3cd; }}
            .metric.poor {{ border-left-color: #dc3545; background-color: #f8d7da; }}
            .observation {{
                margin: 10px 0;
                padding: 10px;
                background-color: #f8f9fa;
                border-left: 3px solid #4472C4;
            }}
            .recommendation {{
                margin: 10px 0;
                padding: 10px;
                background-color: #fff3cd;
                border-left: 3px solid #ffc107;
            }}
            .footer {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #ddd;
                text-align: center;
                font-size: 12px;
                color: #666;
            }}
            @media print {{
                body {{ margin: 0; }}
                .header {{ page-break-after: avoid; }}
                .metric {{ page-break-inside: avoid; }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="title">🚌 RELATÓRIO DE SATISFAÇÃO</div>
            <div class="subtitle">Sistema Municipal de Transporte Coletivo</div>
            <p><strong>Linha:</strong> {relatorio.linha_numero}</p>
            <p>Relatório baseado em {relatorio.total_pesquisas} pesquisas</p>
        </div>
        
        <table class="info-table">
            <tr><th>Período</th><td>{relatorio.periodo_inicio.strftime('%d/%m/%Y')} a {relatorio.periodo_fim.strftime('%d/%m/%Y')}</td></tr>
            <tr><th>Total de Pesquisas</th><td>{relatorio.total_pesquisas}</td></tr>
            <tr><th>Média Geral</th><td>{relatorio.media_geral:.1f}/10 ({relatorio.get_classificacao_geral()})</td></tr>
            <tr><th>Data do Relatório</th><td>{relatorio.data_criacao.strftime('%d/%m/%Y às %H:%M')}</td></tr>
        </table>
        
        <div class="section-title">📈 Análise Detalhada por Categoria</div>
        
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
        <div class="section-title">💬 Observações dos Usuários ({len(observacoes)} comentários)</div>
        """
        for i, obs in enumerate(observacoes, 1):
            html_content += f'<div class="observation"><strong>#{i}:</strong> {obs}</div>'
    else:
        html_content += """
        <div class="section-title">💬 Observações dos Usuários</div>
        <p style="font-style: italic; color: #666;">Nenhuma observação adicional foi fornecida neste período.</p>
        """
    
    # Adicionar recomendações
    recomendacoes = relatorio.get_recomendacoes()
    html_content += """
    <div class="section-title">📋 Recomendações</div>
    """
    for rec in recomendacoes:
        html_content += f'<div class="recommendation">{rec}</div>'
    
    html_content += f"""
        <div class="footer">
            <p>📧 Relatório gerado automaticamente pelo Sistema de Pesquisa de Satisfação</p>
            <p>🌐 Sistema Municipal de Transporte Coletivo | Gerado em {relatorio.data_criacao.strftime('%d/%m/%Y às %H:%M')}</p>
        </div>
    </body>
    </html>
    """
    
    # Criar arquivo temporário
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
        f.write(html_content)
        return f.name

def gerar_word_simples(relatorio):
    """Gera um arquivo HTML formatado para Word"""
    return gerar_pdf_simples(relatorio)  # Mesmo formato HTML

