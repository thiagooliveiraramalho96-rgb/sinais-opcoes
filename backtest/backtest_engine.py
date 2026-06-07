"""
Motor de backtest completo para testar estratégias de opções.
"""
import pandas as pd
import numpy as np
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime

from .trade_simulator import TradeSimulator, TradeResult, ExitConfig
from .metrics import BacktestMetrics
from ..analysis.indicators import IndicatorCalculator
from ..analysis.filters import SignalFilters
from ..analysis.triggers import SignalTriggers
from ..engine.parser import parse
from ..engine.interpreter import Interpretador


@dataclass
class BacktestResult:
    """Resultado consolidado do backtest."""
    ticker: str
    periodo_inicio: str
    periodo_fim: str
    capital_inicial: float
    capital_final: float
    total_operacoes: int
    operacoes_ganhadoras: int
    operacoes_perdedoras: int
    win_rate: float
    lucro_total: float
    lucro_percentual: float
    fator_lucro: float
    drawdown_maximo: float
    sharpe_ratio: float
    media_ganho: float
    media_perda: float
    expectancy: float
    trades: List[TradeResult]
    curva_capital: List[float]


class BacktestEngine:
    """
    Motor de backtest para testar estratégias em dados históricos.
    """
    
    def __init__(self, capital_inicial: float = 10000.0,
                 risco_por_operacao: float = 0.01,
                 config_saida: ExitConfig = None,
                 usar_regra_personalizada: bool = False,
                 formula_entrada: str = None,
                 dias_vencimento: int = 30):
        """
        Args:
            capital_inicial: Capital inicial
            risco_por_operacao: Risco por operação (%)
            config_saida: Configuração de saída
            usar_regra_personalizada: Se True, usa fórmula personalizada
            formula_entrada: Fórmula personalizada de entrada
            dias_vencimento: Dias úteis até vencimento
        """
        self.capital_inicial = capital_inicial
        self.risco_por_operacao = risco_por_operacao
        self.config_saida = config_saida or ExitConfig()
        self.usar_regra_personalizada = usar_regra_personalizada
        self.formula_entrada = formula_entrada
        self.dias_vencimento = dias_vencimento
        self.ast_entrada = None
        
        if usar_regra_personalizada and formula_entrada:
            try:
                self.ast_entrada = parse(formula_entrada)
            except Exception as e:
                print(f"[ERRO] Fórmula inválida: {e}")
    
    def executar(self, ticker: str, dados: pd.DataFrame,
                 data_inicio: str = None, data_fim: str = None) -> BacktestResult:
        """
        Executa backtest em dados históricos.
        
        Args:
            ticker: Ticker do ativo
            dados: DataFrame OHLCV
            data_inicio: Data de início (opcional)
            data_fim: Data de fim (opcional)
        
        Returns:
            BacktestResult com resultados
        """
        if dados.empty or len(dados) < 200:
            raise ValueError("Dados insuficientes para backtest (mínimo 200 candles)")
        
        # Filtrar por data se especificado
        df = dados.copy()
        if data_inicio:
            df = df[df.index >= data_inicio]
        if data_fim:
            df = df[df.index <= data_fim]
        
        if len(df) < 200:
            raise ValueError("Dados insuficientes após filtro de data")
        
        # Calcular indicadores
        calc = IndicatorCalculator(df)
        indicadores = calc.obter_indicadores()
        
        # Preparar simulador
        simulador = TradeSimulator(
            capital_inicial=self.capital_inicial,
            risco_por_operacao=self.risco_por_operacao,
            config_saida=self.config_saida,
            dias_vencimento=self.dias_vencimento
        )
        
        # Loop sobre os dados
        trades = []
        ultimo_sinal_idx = -self.dias_vencimento  # Evitar sinais muito próximos
        
        for idx in range(200, len(df)):
            # Verificar sinal
            tem_sinal = False
            preco_entrada = float(df['Close'].iloc[idx])
            
            if self.usar_regra_personalizada and self.ast_entrada:
                interpretador = Interpretador(df, indicadores)
                tem_sinal = interpretador.avaliar(self.ast_entrada, idx)
            else:
                filtros = SignalFilters(df, indicadores)
                result_filtros = filtros.aplicar_filtros(idx)
                
                if result_filtros['aprovado']:
                    triggers = SignalTriggers(df, indicadores)
                    result_gatilhos = triggers.avaliar_gatilhos(idx)
                    tem_sinal = result_gatilhos['gatilho_ativo']
            
            # Se tem sinal e distância suficiente do último
            if tem_sinal and (idx - ultimo_sinal_idx) >= self.dias_vencimento:
                trade = simulador.simular_trade(idx, preco_entrada, df, ticker)
                trades.append(trade)
                ultimo_sinal_idx = idx
        
        # Calcular métricas
        metricas = BacktestMetrics()
        resultado = metricas.calcular(
            capital_inicial=self.capital_inicial,
            capital_final=simulador.capital,
            trades=trades,
            curva_capital=simulador.capital_historico
        )
        
        return BacktestResult(
            ticker=ticker,
            periodo_inicio=str(df.index[0].date()),
            periodo_fim=str(df.index[-1].date()),
            capital_inicial=self.capital_inicial,
            capital_final=simulador.capital,
            total_operacoes=resultado['total_operacoes'],
            operacoes_ganhadoras=resultado['operacoes_ganhadoras'],
            operacoes_perdedoras=resultado['operacoes_perdedoras'],
            win_rate=resultado['win_rate'],
            lucro_total=resultado['lucro_total'],
            lucro_percentual=resultado['lucro_percentual'],
            fator_lucro=resultado['fator_lucro'],
            drawdown_maximo=resultado['drawdown_maximo'],
            sharpe_ratio=resultado['sharpe_ratio'],
            media_ganho=resultado['media_ganho'],
            media_perda=resultado['media_perda'],
            expectancy=resultado['expectancy'],
            trades=trades,
            curva_capital=simulador.capital_historico
        )