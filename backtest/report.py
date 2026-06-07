"""
Gerador de relatórios de backtest.
"""
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from typing import List
from datetime import datetime
from .backtest_engine import BacktestResult
matplotlib.use('Agg')  # Non-interactive backend


class BacktestReport:
    """Gera relatórios e gráficos do backtest."""
    
    @staticmethod
    def gerar_texto(resultado: BacktestResult) -> str:
        """Gera relatório em texto simples."""
        lines = []
        lines.append("=" * 50)
        lines.append(f"📊 RELATÓRIO DE BACKTEST - {resultado.ticker}")
        lines.append("=" * 50)
        lines.append(f"Período: {resultado.periodo_inicio} a {resultado.periodo_fim}")
        lines.append(f"Capital: R$ {resultado.capital_inicial:.2f} → R$ {resultado.capital_final:.2f}")
        lines.append(f"Lucro: R$ {resultado.lucro_total:.2f} ({resultado.lucro_percentual:.2f}%)")
        lines.append("")
        lines.append("📈 MÉTRICAS:")
        lines.append(f"  Total de operações: {resultado.total_operacoes}")
        lines.append(f"  Operações ganhadoras: {resultado.operacoes_ganhadoras}")
        lines.append(f"  Operações perdedoras: {resultado.operacoes_perdedoras}")
        lines.append(f"  Win rate: {resultado.win_rate:.1f}%")
        lines.append(f"  Fator de lucro: {resultado.fator_lucro:.2f}")
        lines.append(f"  Drawdown máximo: {resultado.drawdown_maximo:.2f}%")
        lines.append(f"  Sharpe ratio: {resultado.sharpe_ratio:.2f}")
        lines.append(f"  Média de ganho: R$ {resultado.media_ganho:.2f}")
        lines.append(f"  Média de perda: R$ {resultado.media_perda:.2f}")
        lines.append(f"  Expectancy: R$ {resultado.expectancy:.2f}")
        lines.append("")
        lines.append("📋 ÚLTIMAS OPERAÇÕES:")
        lines.append(f"  {'Data':<12} {'Tipo':<15} {'Resultado':<10}")
        lines.append("  " + "-" * 40)
        for trade in resultado.trades[-10:]:
            data = trade.data_saida or trade.data_entrada
            if trade.resultado_abs is not None:
                sinal = "+" if trade.resultado_abs > 0 else ""
                lines.append(f"  {str(data.date()):<12} {trade.tipo_saida:<15} {sinal}R$ {trade.resultado_abs:<8.2f}")
        lines.append("")
        return "\n".join(lines)
    
    @staticmethod
    def gerar_grafico(resultado: BacktestResult, salvar_em: str = None):
        """Gera gráfico da curva de capital."""
        if not resultado.curva_capital:
            return None
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        
        # Curva de capital
        capital = resultado.curva_capital
        initial = resultado.capital_inicial
        capital_pct = [(c / initial - 1) * 100 for c in capital]
        
        ax1.plot(capital_pct, color='green', linewidth=1.5)
        ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
        ax1.set_title(f'Curva de Capital - {resultado.ticker}')
        ax1.set_ylabel('Retorno (%)')
        ax1.grid(True, alpha=0.3)
        
        # Drawdown
        pico = initial
        drawdowns = []
        for c in capital:
            if c > pico:
                pico = c
            dd = (pico - c) / pico * 100
            drawdowns.append(-dd)
        
        ax2.fill_between(range(len(drawdowns)), drawdowns, 0, 
                         color='red', alpha=0.3, label='Drawdown')
        ax2.set_title('Drawdown')
        ax2.set_ylabel('Drawdown (%)')
        ax2.set_xlabel('Operações')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if salvar_em:
            plt.savefig(salvar_em, dpi=100, bbox_inches='tight')
        
        return fig