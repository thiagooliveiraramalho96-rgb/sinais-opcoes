"""
Motor principal de análise de sinais.

Integra data_fetcher, indicators, filters, triggers e engine de fórmulas.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional, List

from .data_fetcher import DataFetcher
from .indicators import IndicatorCalculator
from .filters import SignalFilters
from .triggers import SignalTriggers
from ..engine.parser import parse
from ..engine.interpreter import Interpretador


@dataclass
class SinalResultado:
    """Resultado completo de uma análise de sinal."""
    ticker: str
    timestamp: datetime
    preco_atual: float
    mm20: float
    mm50: float
    mm200: float
    adx: float
    ifr: float
    tipo_entrada: Optional[str]  # 'Pullback MM20', 'Rompimento de Topo', None
    distancia_mm20_pct: float
    filtros_aprovados: bool
    gatilho_ativo: bool
    sinal_verde: bool
    detalhes_filtros: dict
    detalhes_gatilhos: dict
    mensagem: str
    
    def para_dict(self) -> dict:
        """Converte para dicionário para exibição."""
        return {
            'Ticker': self.ticker,
            'Preço atual': f"R$ {self.preco_atual:.2f}",
            'MM20': f"R$ {self.mm20:.2f}",
            'MM50': f"R$ {self.mm50:.2f}",
            'MM200': f"R$ {self.mm200:.2f}",
            'ADX': f"{self.adx:.2f}",
            'IFR': f"{self.ifr:.2f}",
            'Tipo de entrada': self.tipo_entrada or 'Nenhum',
            'Distância para MM20': f"{self.distancia_mm20_pct:.2f}%",
            'Dias para vencimento': '20 a 40 dias úteis',
            'Status': '✅ SINAL VERDE' if self.sinal_verde else '❌ Sem sinal',
        }


class SignalEngine:
    """
    Motor completo de análise de sinais.
    Suporta estratégia padrão e regras personalizadas via fórmula.
    """
    
    def __init__(self, usar_regra_personalizada: bool = False, 
                 formula_entrada: str = None,
                 formula_saida: str = None):
        """
        Args:
            usar_regra_personalizada: Se True, usa a fórmula personalizada
            formula_entrada: Fórmula/regra personalizada de entrada
            formula_saida: Configuração de saída personalizada
        """
        self.usar_regra_personalizada = usar_regra_personalizada
        self.formula_entrada = formula_entrada
        self.formula_saida = formula_saida
        self.ast_entrada = None
        
        if usar_regra_personalizada and formula_entrada:
            try:
                self.ast_entrada = parse(formula_entrada)
            except SyntaxError as e:
                print(f"[ERRO] Fórmula inválida: {e}")
    
    def analisar(self, ticker: str, dados: pd.DataFrame) -> SinalResultado:
        """
        Analisa um ativo e retorna o resultado do sinal.
        
        Args:
            ticker: Ticker do ativo (ex: 'PETR4.SA')
            dados: DataFrame OHLCV
        
        Returns:
            SinalResultado com todas as informações
        """
        if dados.empty or len(dados) < 200:
            return self._sinal_vazio(ticker, "Dados insuficientes")
        
        # Calcular indicadores
        calc = IndicatorCalculator(dados)
        indicadores = calc.obter_indicadores()
        
        # Último índice
        idx = len(dados) - 1
        df = dados
        
        preco_atual = float(df['Close'].iloc[idx])
        mm20 = float(indicadores['MM20'].iloc[idx]) if not pd.isna(indicadores['MM20'].iloc[idx]) else 0
        mm50 = float(indicadores['MM50'].iloc[idx]) if not pd.isna(indicadores['MM50'].iloc[idx]) else 0
        mm200 = float(indicadores['MM200'].iloc[idx]) if not pd.isna(indicadores['MM200'].iloc[idx]) else 0
        adx = float(indicadores['ADX'].iloc[idx]) if not pd.isna(indicadores['ADX'].iloc[idx]) else 0
        ifr = float(indicadores['IFR'].iloc[idx]) if not pd.isna(indicadores['IFR'].iloc[idx]) else 0
        
        distancia_mm20 = abs(preco_atual - mm20) / mm20 * 100 if mm20 > 0 else 0
        
        if self.usar_regra_personalizada and self.ast_entrada:
            # Usar regra personalizada
            interpretador = Interpretador(dados, indicadores)
            sinal_personalizado = interpretador.avaliar(self.ast_entrada, idx)
            
            # Para regra personalizada, consideramos filtros como parte da fórmula
            return SinalResultado(
                ticker=ticker,
                timestamp=datetime.now(),
                preco_atual=preco_atual,
                mm20=mm20,
                mm50=mm50,
                mm200=mm200,
                adx=adx,
                ifr=ifr,
                tipo_entrada='Regra Personalizada' if sinal_personalizado else None,
                distancia_mm20_pct=distancia_mm20,
                filtros_aprovados=bool(sinal_personalizado),
                gatilho_ativo=bool(sinal_personalizado),
                sinal_verde=bool(sinal_personalizado),
                detalhes_filtros={'regra_personalizada': bool(sinal_personalizado)},
                detalhes_gatilhos={'regra_personalizada': bool(sinal_personalizado)},
                mensagem='✅ Sinal VERDE (Regra Personalizada)' if sinal_personalizado else '❌ Regra personalizada não ativada'
            )
        else:
            # Usar estratégia padrão
            filtros = SignalFilters(dados, indicadores)
            resultado_filtros = filtros.aplicar_filtros(idx)
            
            triggers = SignalTriggers(dados, indicadores)
            resultado_gatilhos = triggers.avaliar_gatilhos(idx)
            
            sinal_verde = resultado_filtros['aprovado'] and resultado_gatilhos['gatilho_ativo']
            
            return SinalResultado(
                ticker=ticker,
                timestamp=datetime.now(),
                preco_atual=preco_atual,
                mm20=mm20,
                mm50=mm50,
                mm200=mm200,
                adx=adx,
                ifr=ifr,
                tipo_entrada=resultado_gatilhos['tipo_entrada'],
                distancia_mm20_pct=distancia_mm20,
                filtros_aprovados=resultado_filtros['aprovado'],
                gatilho_ativo=resultado_gatilhos['gatilho_ativo'],
                sinal_verde=sinal_verde,
                detalhes_filtros=resultado_filtros['detalhes'],
                detalhes_gatilhos=resultado_gatilhos,
                mensagem=resultado_filtros['mensagem']
            )
    
    def analisar_multiplos(self, dados_dict: dict) -> List[SinalResultado]:
        """
        Analisa múltiplos ativos.
        
        Args:
            dados_dict: Dict {ticker: DataFrame}
        
        Returns:
            Lista de SinalResultado
        """
        resultados = []
        for ticker, dados in dados_dict.items():
            resultado = self.analisar(ticker, dados)
            resultados.append(resultado)
        return resultados
    
    def _sinal_vazio(self, ticker: str, motivo: str) -> SinalResultado:
        """Retorna resultado vazio para quando não há dados suficientes."""
        return SinalResultado(
            ticker=ticker,
            timestamp=datetime.now(),
            preco_atual=0,
            mm20=0, mm50=0, mm200=0,
            adx=0, ifr=0,
            tipo_entrada=None,
            distancia_mm20_pct=0,
            filtros_aprovados=False,
            gatilho_ativo=False,
            sinal_verde=False,
            detalhes_filtros={},
            detalhes_gatilhos={},
            mensagem=f"❌ {motivo}"
        )