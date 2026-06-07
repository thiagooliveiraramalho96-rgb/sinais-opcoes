"""
Fetcher de dados financeiros usando yfinance.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class DataFetcher:
    """
    Baixa dados históricos de ativos da B3 via Yahoo Finance.
    """
    
    # Lista padrão de ativos da B3
    TICKERS_PADRAO = [
        'PETR4.SA', 'VALE3.SA', 'ITUB4.SA', 'BBDC4.SA', 'ABEV3.SA',
        'BBAS3.SA', 'B3SA3.SA', 'WEGE3.SA', 'RENT3.SA', 'RADL3.SA',
        'LREN3.SA', 'MGLU3.SA', 'VIIA3.SA', 'PCAR3.SA', 'AMER3.SA',
        'CVCB3.SA', 'GOLL4.SA', 'AZUL4.SA', 'EMBR3.SA', 'SUZB3.SA',
        'JBSS3.SA', 'MRFG3.SA', 'BEEF3.SA', 'PRIO3.SA', 'PETR3.SA',
        'CSAN3.SA', 'UGPA3.SA', 'VBBR3.SA', 'CMIG3.SA', 'CMIG4.SA',
        'ELET3.SA', 'ELET6.SA', 'NEOE3.SA', 'EGIE3.SA', 'TAEE3.SA',
        'ENGI11.SA', 'SANB11.SA', 'BPAC11.SA', 'ITSA4.SA', 'EQTL3.SA',
        'CPLE6.SA', 'SAPR11.SA', 'HYPE3.SA', 'TOTS3.SA', 'QUAL3.SA',
        'FLRY3.SA', 'HAPV3.SA', 'RDOR3.SA', 'ALOS3.SA', 'NTCO3.SA',
    ]
    
    def __init__(self, periodo_dias: int = 365 * 2):
        """
        Args:
            periodo_dias: Quantos dias de dados históricos baixar
        """
        self.periodo_dias = periodo_dias
        self.data_inicio = (datetime.now() - timedelta(days=periodo_dias)).strftime('%Y-%m-%d')
        self.data_fim = datetime.now().strftime('%Y-%m-%d')
    
    def baixar_dados(self, ticker: str, periodo: str = None) -> pd.DataFrame:
        """
        Baixa dados OHLCV de um ticker.
        
        Args:
            ticker: Ticker do ativo (ex: 'PETR4.SA')
            periodo: Período yfinance (ex: '2y', '1y', '6mo')
                     Se None, usa o periodo_dias configurado
        
        Returns:
            DataFrame com colunas Open, High, Low, Close, Volume
        """
        try:
            ticker_obj = yf.Ticker(ticker)
            
            if periodo:
                dados = ticker_obj.history(period=periodo)
            else:
                dados = ticker_obj.history(
                    start=self.data_inicio,
                    end=self.data_fim
                )
            
            if dados.empty:
                print(f"[AVISO] Sem dados para {ticker}")
                return pd.DataFrame()
            
            # Garantir colunas padrão
            colunas = {'Open', 'High', 'Low', 'Close', 'Volume'}
            if not colunas.issubset(dados.columns):
                print(f"[AVISO] Colunas faltando para {ticker}: {colunas - set(dados.columns)}")
                return pd.DataFrame()
            
            # Limpar dados
            dados = dados.dropna()
            
            return dados
            
        except Exception as e:
            print(f"[ERRO] Falha ao baixar {ticker}: {e}")
            return pd.DataFrame()
    
    def baixar_multiplos(self, tickers: list) -> dict:
        """
        Baixa dados de múltiplos tickers.
        
        Returns:
            Dict {ticker: DataFrame}
        """
        resultados = {}
        for ticker in tickers:
            dados = self.baixar_dados(ticker)
            if not dados.empty:
                resultados[ticker] = dados
                print(f"[OK] {ticker}: {len(dados)} candles baixados")
            else:
                print(f"[FALHA] {ticker}: sem dados")
        return resultados
    
    @staticmethod
    def formatar_ticker(ticker: str) -> str:
        """Garante que o ticker tenha o sufixo .SA para B3."""
        ticker = ticker.upper().strip()
        if not ticker.endswith('.SA'):
            ticker += '.SA'
        return ticker