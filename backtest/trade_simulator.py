"""
Simulador de trades para backtest.
"""
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

from .option_pricing import OptionPricing


@dataclass
class TradeResult:
    """Resultado de uma operação simulada."""
    entrada_idx: int
    saida_idx: Optional[int]
    preco_entrada: float
    preco_saida: Optional[float]
    premio_pago: float
    premio_recebido: Optional[float]
    resultado_pct: Optional[float]
    resultado_abs: Optional[float]
    data_entrada: pd.Timestamp
    data_saida: Optional[pd.Timestamp]
    tipo_saida: str  # 'stop', 'parcial', 'total', 'vencimento'
    motivo: str = ''
    ativo: str = ''


@dataclass
class ExitConfig:
    """Configuração de saída da operação."""
    stop_perda_pct: float = 0.50  # 50% do prêmio
    realizacao_parcial_pct: float = 1.00  # +100%
    saida_total_min_pct: float = 1.50  # +150%
    saida_total_max_pct: float = 2.00  # +200%


class TradeSimulator:
    """
    Simula a execução de trades com base em sinais.
    """
    
    def __init__(self, capital_inicial: float = 10000.0,
                 risco_por_operacao: float = 0.01,
                 custo_por_operacao: float = 5.0,
                 config_saida: ExitConfig = None,
                 dias_vencimento: int = 30):
        """
        Args:
            capital_inicial: Capital inicial para backtest
            risco_por_operacao: % do capital arriscado por operação
            custo_por_operacao: Custo fixo por operação (corretagem, etc.)
            config_saida: Configuração de saída
            dias_vencimento: Dias úteis até vencimento
        """
        self.capital_inicial = capital_inicial
        self.capital = capital_inicial
        self.risco_por_operacao = risco_por_operacao
        self.custo_por_operacao = custo_por_operacao
        self.config_saida = config_saida or ExitConfig()
        self.dias_vencimento = dias_vencimento
        self.trades: List[TradeResult] = []
        self.capital_historico: List[float] = []
    
    def simular_trade(self, idx_entrada: int, preco_ativo: float, 
                      dados: pd.DataFrame, ticker: str = '') -> TradeResult:
        """
        Simula um trade de CALL ATM.
        
        Args:
            idx_entrada: Índice do candle de entrada
            preco_ativo: Preço do ativo no momento da entrada
            dados: DataFrame completo OHLCV
            ticker: Nome do ticker
        
        Returns:
            TradeResult com resultado da operação
        """
        premio_pct = OptionPricing.estimar_premio_percentual(self.dias_vencimento)
        premio_pago = preco_ativo * premio_pct
        
        # Calcular tamanho da posição com base no risco
        valor_risco = self.capital * self.risco_por_operacao
        stop_premio = premio_pago * self.config_saida.stop_perda_pct
        qtd_contratos = max(1, int(valor_risco / stop_premio))
        investimento_total = premio_pago * qtd_contratos + self.custo_por_operacao
        
        # Verificar se tem capital suficiente
        if investimento_total > self.capital:
            qtd_contratos = max(0, int((self.capital - self.custo_por_operacao) / premio_pago))
            if qtd_contratos <= 0:
                return TradeResult(
                    entrada_idx=idx_entrada, saida_idx=None,
                    preco_entrada=preco_ativo, preco_saida=None,
                    premio_pago=premio_pago, premio_recebido=None,
                    resultado_pct=None, resultado_abs=None,
                    data_entrada=dados.index[idx_entrada], data_saida=None,
                    tipo_saida='sem_capital', motivo='Capital insuficiente',
                    ativo=ticker
                )
            investimento_total = premio_pago * qtd_contratos + self.custo_por_operacao
        
        # Simular saída
        data_entrada = dados.index[idx_entrada]
        idx_fim = min(idx_entrada + self.dias_vencimento, len(dados) - 1)
        
        for idx in range(idx_entrada + 1, idx_fim + 1):
            preco_atual = dados['Close'].iloc[idx]
            
            # Calcular variação do prêmio (simplificado: mesma proporção do ativo)
            variacao_ativo = (preco_atual - preco_ativo) / preco_ativo
            premio_atual = premio_pago * (1 + variacao_ativo * 2)  # Alavancagem ~2x
            resultado_pct = (premio_atual - premio_pago) / premio_pago
            
            # Verificar stop (perda de 50% do prêmio)
            if resultado_pct <= -self.config_saida.stop_perda_pct:
                premio_recebido = premio_atual
                resultado_pct = -self.config_saida.stop_perda_pct
                resultado_abs = -premio_pago * self.config_saida.stop_perda_pct * qtd_contratos - self.custo_por_operacao
                self.capital += resultado_abs
                self.capital_historico.append(self.capital)
                return TradeResult(
                    entrada_idx=idx_entrada, saida_idx=idx,
                    preco_entrada=preco_ativo, preco_saida=preco_atual,
                    premio_pago=premio_pago, premio_recebido=premio_recebido,
                    resultado_pct=resultado_pct, resultado_abs=resultado_abs,
                    data_entrada=data_entrada, data_saida=dados.index[idx],
                    tipo_saida='stop', motivo=f'Stop Loss acionado (-{self.config_saida.stop_perda_pct*100:.0f}%)',
                    ativo=ticker
                )
            
            # Verificar realização parcial (+100%)
            if resultado_pct >= self.config_saida.realizacao_parcial_pct:
                # Realizar metade
                premio_recebido = premio_atual * 0.5  # Vender metade
                resultado_abs = (premio_recebido - premio_pago * 0.5) * qtd_contratos - self.custo_por_operacao
                self.capital += resultado_abs
                self.capital_historico.append(self.capital)
                return TradeResult(
                    entrada_idx=idx_entrada, saida_idx=idx,
                    preco_entrada=preco_ativo, preco_saida=preco_atual,
                    premio_pago=premio_pago, premio_recebido=premio_recebido,
                    resultado_pct=resultado_pct, resultado_abs=resultado_abs,
                    data_entrada=data_entrada, data_saida=dados.index[idx],
                    tipo_saida='parcial', motivo=f'Realização parcial (+{resultado_pct*100:.0f}%)',
                    ativo=ticker
                )
        
        # Saída no vencimento
        preco_vencimento = dados['Close'].iloc[idx_fim]
        variacao_total = (preco_vencimento - preco_ativo) / preco_ativo
        premio_final = premio_pago * (1 + variacao_total * 2)
        resultado_pct = (premio_final - premio_pago) / premio_pago
        
        resultado_abs = (premio_final - premio_pago) * qtd_contratos - self.custo_por_operacao
        
        if resultado_pct >= self.config_saida.saida_total_min_pct:
            tipo_saida = 'total_ganho'
            motivo = f'Saída total (+{resultado_pct*100:.0f}%)'
        else:
            tipo_saida = 'vencimento'
            motivo = f'Vencimento ({resultado_pct*100:.0f}%)'
        
        self.capital += resultado_abs
        self.capital_historico.append(self.capital)
        
        return TradeResult(
            entrada_idx=idx_entrada, saida_idx=idx_fim,
            preco_entrada=preco_ativo, preco_saida=preco_vencimento,
            premio_pago=premio_pago, premio_recebido=premio_final,
            resultado_pct=resultado_pct, resultado_abs=resultado_abs,
            data_entrada=data_entrada, data_saida=dados.index[idx_fim],
            tipo_saida=tipo_saida, motivo=motivo,
            ativo=ticker
        )
    
    def reset(self):
        """Reseta o simulador para estado inicial."""
        self.capital = self.capital_inicial
        self.trades = []
        self.capital_historico = [self.capital]