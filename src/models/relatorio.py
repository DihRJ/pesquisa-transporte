from src.database import db
from datetime import datetime
import json

class Relatorio(db.Model):
    __tablename__ = 'relatorios'
    
    id = db.Column(db.Integer, primary_key=True)
    linha_numero = db.Column(db.String(100), nullable=False, index=True)
    # Use local time for report creation date to respect configured timezone
    data_criacao = db.Column(db.DateTime, default=datetime.now, nullable=False)
    periodo_inicio = db.Column(db.DateTime, nullable=False)
    periodo_fim = db.Column(db.DateTime, nullable=False)
    total_pesquisas = db.Column(db.Integer, nullable=False)
    
    # Estatísticas calculadas
    media_pontualidade = db.Column(db.Float, nullable=False)
    media_frequencia = db.Column(db.Float, nullable=False)
    media_conforto = db.Column(db.Float, nullable=False)
    media_atendimento = db.Column(db.Float, nullable=False)
    media_infraestrutura = db.Column(db.Float, nullable=False)
    media_geral = db.Column(db.Float, nullable=False)
    
    # Dados das pesquisas em JSON
    dados_pesquisas = db.Column(db.Text, nullable=False)  # JSON com todas as pesquisas
    observacoes = db.Column(db.Text)  # Observações concatenadas
    
    # Status do relatório
    processado = db.Column(db.Boolean, default=True, nullable=False)
    
    def __init__(self, linha_numero, pesquisas):
        self.linha_numero = linha_numero
        self.total_pesquisas = len(pesquisas)
        
        # Calcular período
        datas = [p.data_criacao for p in pesquisas]
        self.periodo_inicio = min(datas)
        self.periodo_fim = max(datas)
        
        # Calcular médias
        self.media_pontualidade = sum(p.pontualidade for p in pesquisas) / len(pesquisas)
        self.media_frequencia = sum(p.frequencia for p in pesquisas) / len(pesquisas)
        self.media_conforto = sum(p.conforto for p in pesquisas) / len(pesquisas)
        self.media_atendimento = sum(p.atendimento for p in pesquisas) / len(pesquisas)
        self.media_infraestrutura = sum(p.infraestrutura for p in pesquisas) / len(pesquisas)
        self.media_geral = (self.media_pontualidade + self.media_frequencia + 
                           self.media_conforto + self.media_atendimento + 
                           self.media_infraestrutura) / 5
        
        # Armazenar dados das pesquisas
        dados = []
        observacoes_lista = []
        
        for p in pesquisas:
            dados.append({
                'id': p.id,
                'data_criacao': p.data_criacao.isoformat(),
                'linha_itinerario': p.linha_itinerario,
                'pontualidade': p.pontualidade,
                'frequencia': p.frequencia,
                'conforto': p.conforto,
                'atendimento': p.atendimento,
                'infraestrutura': p.infraestrutura,
                'observacoes': p.observacoes
            })
            
            if p.observacoes and p.observacoes.strip():
                observacoes_lista.append(p.observacoes.strip())
        
        self.dados_pesquisas = json.dumps(dados, ensure_ascii=False)
        self.observacoes = '\n---\n'.join(observacoes_lista) if observacoes_lista else None
    
    def get_dados_pesquisas(self):
        """Retorna os dados das pesquisas como lista de dicionários"""
        return json.loads(self.dados_pesquisas)
    
    def get_observacoes_lista(self):
        """Retorna as observações como lista"""
        if not self.observacoes:
            return []
        return [obs.strip() for obs in self.observacoes.split('---') if obs.strip()]
    
    def classificar_nota(self, nota):
        """Classifica uma nota em categoria"""
        if nota >= 9: return "Excelente"
        elif nota >= 7: return "Bom"
        elif nota >= 4: return "Regular"
        else: return "Ruim"
    
    def get_classificacao_geral(self):
        """Retorna a classificação geral do relatório"""
        return self.classificar_nota(self.media_geral)
    
    def get_recomendacoes(self):
        """Gera recomendações baseadas nas notas"""
        recomendacoes = []
        
        if self.media_pontualidade < 6:
            recomendacoes.append("🔴 Pontualidade: Revisar horários e implementar monitoramento em tempo real.")
        if self.media_frequencia < 6:
            recomendacoes.append("🔴 Frequência: Avaliar aumento da frota ou otimização das rotas.")
        if self.media_conforto < 6:
            recomendacoes.append("🔴 Conforto: Intensificar manutenção preventiva e limpeza dos veículos.")
        if self.media_atendimento < 6:
            recomendacoes.append("🔴 Atendimento: Implementar treinamento para motoristas e cobradores.")
        if self.media_infraestrutura < 6:
            recomendacoes.append("🔴 Infraestrutura: Melhorar pontos de ônibus e terminais.")
        
        if self.media_geral >= 7:
            recomendacoes.append("✅ Parabéns! A linha apresenta boa avaliação geral. Manter o padrão de qualidade.")
        
        return recomendacoes
    
    def to_dict(self):
        """Converte o relatório para dicionário"""
        return {
            'id': self.id,
            'linha_numero': self.linha_numero,
            'data_criacao': self.data_criacao.isoformat(),
            'periodo_inicio': self.periodo_inicio.isoformat(),
            'periodo_fim': self.periodo_fim.isoformat(),
            'total_pesquisas': self.total_pesquisas,
            'media_pontualidade': round(self.media_pontualidade, 1),
            'media_frequencia': round(self.media_frequencia, 1),
            'media_conforto': round(self.media_conforto, 1),
            'media_atendimento': round(self.media_atendimento, 1),
            'media_infraestrutura': round(self.media_infraestrutura, 1),
            'media_geral': round(self.media_geral, 1),
            'classificacao_geral': self.get_classificacao_geral(),
            'observacoes_count': len(self.get_observacoes_lista()),
            'recomendacoes': self.get_recomendacoes(),
            'processado': self.processado
        }
    
    @staticmethod
    def criar_relatorio_automatico(linha_numero, pesquisas):
        """Cria um relatório automático para uma linha"""
        if len(pesquisas) < 1:
            return None
        
        relatorio = Relatorio(linha_numero, pesquisas)
        db.session.add(relatorio)
        db.session.commit()
        
        print(f"📊 Relatório automático criado para linha {linha_numero}")
        print(f"   📈 Média geral: {relatorio.media_geral:.1f}/10")
        print(f"   📅 Período: {relatorio.periodo_inicio.strftime('%d/%m/%Y')} a {relatorio.periodo_fim.strftime('%d/%m/%Y')}")
        
        return relatorio

