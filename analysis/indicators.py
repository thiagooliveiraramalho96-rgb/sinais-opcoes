"""
Calculadora de indicadores técnicos.
"""
import pandas as pd
import numpy as np
import pandas_ta as ta


class IndicatorCalculator:
    """
    Calcula indicadores técnicos para análise de sinais.
    """
    
    def __init__(self, dados: pd.DataFrame):
        """
        Args:
            dados: DataFrame com colunas Open, High, Low, Close, Volume
        """
        self.dados = dados
        self._indicadores = {}
        self._calcular_todos()
    
    def _calcular_todos(self):
        """Calcula todos os indicadores necessários."""
        if self.dados.empty:
            return
        
        df = self.dados
        
        # Médias Móveis
        self._indicadores['MM20'] = ta.sma(df['Close'], length=20)
        self._indicadores['MM50'] = ta.sma(df['Close'], length=50)
        self._indicadores['MM200'] = ta.sma(df['Close'], length=200)
        
        # ADX (14)
        adx_df = ta.adx(df['High'], df['Low'], df['Close'], length=14)
        if adx_df is not None and not adx_df.empty:
            # Procurar a coluna ADX (pode ter nomes diferentes)
            for col in adx_df.columns:
                if 'ADX' in col.upper():
                    self._indicadores['ADX'] = adx_df[col]
                    break
            if 'ADX' not in self._indicadores:
                # Fallback: pegar a primeira coluna
                self._indicadores['ADX'] = adx_df.iloc[:, 0]
        
        # IFR / RSI (14)
        rsi = ta.rsi(df['Close'], length=14)
        if rsi is not None:
            self._indicadores['IFR'] = rsi
            self._indicadores['RSI'] = rsi
        
        # Volume médio (20)
        self._indicadores['VOLMEAN20'] = df['Volume'].rolling(window=20).mean()
        
        # Topo20 - maior fechamento dos últimos 20
        self._indicadores['TOPO20'] = df['Close'].rolling(window=20).max()
        
        # Gap percentual
        self._indicadores['GAP'] = self._calcular_gap_serie()
        
        # Variação percentual diária
        self._indicadores['RET'] = df['Close'].pct_change() * 100
    
    def _calcular_gap_serie(self) -> pd.Series:
        """Calcula gap percentual para toda a série."""
        df = self.dados
        gap = pd.Series(0.0, index=df.index)
        prev_close = df['Close'].shift(1)
        gap = (df['Low'] - prev_close) / prev_close * 100
        gap = gap.fillna(0.0)
        return gap
    
    def obter_indicadores(self) -> dict:
        """
        Retorna dicionário com todos os indicadores calculados.
        
        Returns:
            dict: {'MM20': Series, 'MM50': Series, ...}
        """
        return self._indicadores.copy()
    
    def obter_indicador(self, nome: str) -> pd.Series:
        """Obtém um indicador específico pelo nome."""
        return self._indicadores.get(nome, pd.Series(dtype=float))
    
    def obter_indicador_no_indice(self, nome: str, idx: int) -> float:
        """Obtém valor do indicador em um índice específico."""
        serie = self._indicadores.get(nome)
        if serie is None or idx >= len(serie):
            return float('nan')
        valor = serie.iloc[idx]
        return float(valor) if not pd.isna(valor) else float('nan')