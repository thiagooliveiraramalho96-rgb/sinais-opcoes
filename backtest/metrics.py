"""
Cálculo de métricas de desempenho para backtest.
"""
import numpy as np
import pandas as pd
from typing import List
from .trade_simulator import TradeResult


class BacktestMetrics:
    """
    Calcula métricas de desempenho a partir dos resultados do backtest.
    """
    
    @staticmethod
    def calcular(capital_inicial: float, capital_final: float,
                 trades: List[TradeResult], curva_capital: List[float]) -> dict:
        """
        Calcula todas as métricas do backtest.
        
        Returns:
            dict com todas as métricas
        """
        if not trades:
            return {
                'total_operacoes': 0,
                'operacoes_ganhadoras': 0,
                'operacoes_perdedoras': 0,
                'win_rate': 0.0,
                'lucro_total': 0.0,
                'lucro_percentual': 0.0,
                'fator_lucro': 1.0,
                'drawdown_maximo': 0.0,
                'sharpe_ratio': 0.0,
                'media_ganho': 0.0,
                'media_perda': 0.0,
                'expectancy': 0.0,
            }
        
        # Operações ganhadoras e perdedoras
        trades_com_resultado = [t for t in trades if t.resultado_abs is not None]
        ganhadoras = [t for t in trades_com_resultado if t.resultado_abs > 0]
        perdedoras = [t for t in trades_com_resultado if t.resultado_abs <= 0]
        
        total_ops = len(trades_com_resultado)
        win_rate = len(ganhadoras) / total_ops * 100 if total_ops > 0 else 0
        
        # Lucro total
        lucro_total = capital_final - capital_inicial
        lucro_percentual = (lucro_total / capital_inicial) * 100 if capital_inicial > 0 else 0
        
        # Fator de lucro
        bruto_ganho = sum(t.resultado_abs for t in ganhadoras) if ganhadoras else 0
        bruto_perda = abs(sum(t.resultado_abs for t in perdedoras)) if perdedoras else 0
        fator_lucro = bruto_ganho / bruto_perda if bruto_perda > 0 else float('inf')
        
        # Drawdown máximo
        drawdown = BacktestMetrics._calcular_drawdown_maximo(curva_capital, capital_inicial)
        
        # Sharpe ratio
        sharpe = BacktestMetrics._calcular_sharpe(trades_com_resultado)
        
        # Média de ganho e perda
        media_ganho = np.mean([t.resultado_abs for t in ganhadoras]) if ganhadoras else 0
        media_perda = np.mean([abs(t.resultado_abs) for t in perdedoras]) if perdedoras else 0
        
        # Expectancy
        prob_ganho = win_rate / 100
        prob_perda = 1 - prob_ganho
        expectancy = (prob_ganho * media_ganho - prob_perda * media_perda) if media_perda > 0 else media_ganho
        
        return {
            'total_operacoes': total_ops,
            'operacoes_ganhadoras': len(ganhadoras),
            'operacoes_perdedoras': len(perdedoras),
            'win_rate': round(win_rate, 2),
            'lucro_total': round(lucro_total, 2),
            'lucro_percentual': round(lucro_percentual, 2),
            'fator_lucro': round(fator_lucro, 2) if fator_lucro != float('inf') else float('inf'),
            'drawdown_maximo': round(drawdown, 2),
            'sharpe_ratio': round(sharpe, 2),
            'media_ganho': round(media_ganho, 2),
            'media_perda': round(media_perda, 2),
            'expectancy': round(expectancy, 2),
        }
    
    @staticmethod
    def _calcular_drawdown_maximo(curva_capital: List[float], capital_inicial: float) -> float:
        """Calcula o drawdown máximo percentual."""
        if not curva_capital:
            return 0.0
        
        pico = capital_inicial
        drawdown_max = 0.0
        
        for valor in curva_capital:
            if valor > pico:
                pico = valor
            drawdown = (pico - valor) / pico * 100
            if drawdown > drawdown_max:
                drawdown_max = drawdown
        
        return drawdown_max
    
    @staticmethod
    def _calcular_sharpe(trades: List[TradeResult]) -> float:
        """Calcula o Sharpe ratio anualizado."""
        if len(trades) < 2:
            return 0.0
        
        retornos = [t.resultado_pct for t in trades if t.resultado_pct is not None]
        
        if len(retornos) < 2:
            return 0.0
        
        retornos = np.array(retornos)
        media_retorno = np.mean(retornos)
        std_retorno = np.std(retornos)
        
        if std_retorno == 0:
            return 0.0
        
        # Sharpe ratio diário, anualizado
        sharpe_diario = media_retorno / std_retorno
        sharpe_anual = sharpe_diario * np.sqrt(252)
        
        return sharpe_anual