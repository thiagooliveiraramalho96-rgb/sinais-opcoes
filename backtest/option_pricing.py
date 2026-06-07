"""
Precificação simplificada de opções usando Black-Scholes.
"""
import numpy as np
from scipy.stats import norm
import pandas as pd


class OptionPricing:
    """
    Modelo simplificado para estimar prêmio de opções.
    """
    
    @staticmethod
    def black_scholes_call(S: float, K: float, T: float, r: float, sigma: float) -> float:
        """
        Preço de CALL pelo modelo Black-Scholes.
        
        Args:
            S: Preço do ativo subjacente
            K: Strike price
            T: Tempo até vencimento (em anos)
            r: Taxa de juros livre de risco
            sigma: Volatilidade anualizada
        
        Returns:
            Prêmio teórico da CALL
        """
        if T <= 0:
            return max(0, S - K)
        
        d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * np.sqrt(T))
        d2 = d1 - sigma * np.sqrt(T)
        
        call_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
        return max(call_price, 0)
    
    @staticmethod
    def estimar_premio_call_atm(preco_ativo: float, dias_vencimento: int, 
                                  volatilidade: float = 0.30) -> float:
        """
        Estima o prêmio de uma CALL ATM.
        
        Args:
            preco_ativo: Preço atual do ativo
            dias_vencimento: Dias úteis até o vencimento
            volatilidade: Volatilidade anual estimada (default 30%)
        
        Returns:
            Prêmio estimado da CALL ATM
        """
        S = preco_ativo
        K = preco_ativo  # ATM
        T = dias_vencimento / 252  # Converter dias úteis para anos
        r = 0.1325  # Selic ~13.25% ao ano
        
        premio = OptionPricing.black_scholes_call(S, K, T, r, volatilidade)
        return premio
    
    @staticmethod
    def estimar_premio_percentual(dias_vencimento: int, volatilidade: float = 0.30) -> float:
        """
        Estima o prêmio como percentual do preço do ativo.
        
        Para CALL ATM com 20-40 dias úteis, o prêmio costuma ser
        entre 1% e 4% do preço do ativo.
        
        Returns:
            Percentual estimado (ex: 0.025 = 2.5%)
        """
        T = dias_vencimento / 252
        r = 0.1325
        
        # Aproximação simplificada usando volatilidade passada como parâmetro
        premio_pct = 0.4 * volatilidade * np.sqrt(T) + 0.5 * T * r
        return min(max(premio_pct, 0.01), 0.06)  # Limitar entre 1% e 6%
    
    @staticmethod
    def calcular_volatilidade_historica(precos: pd.Series) -> float:
        """Calcula volatilidade histórica anualizada."""
        if len(precos) < 20:
            return 0.30
        
        retornos = np.log(precos / precos.shift(1)).dropna()
        volatilidade = retornos.std() * np.sqrt(252)
        return float(volatilidade)