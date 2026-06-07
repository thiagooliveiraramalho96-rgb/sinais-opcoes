"""
Gatilhos de entrada para geração de sinais.
"""
import pandas as pd
import numpy as np


class SignalTriggers:
    """
    Avalia os gatilhos de entrada: Pullback MM20 e Rompimento de Topo.
    """
    
    def __init__(self, dados: pd.DataFrame, indicadores: dict):
        """
        Args:
            dados: DataFrame OHLCV
            indicadores: Dict com indicadores calculados
        """
        self.dados = dados
        self.indicadores = indicadores
    
    def avaliar_gatilho_pullback(self, idx: int) -> dict:
        """
        Gatilho A: Pullback MM20
        
        Critérios:
        - Mínima do candle atual <= MM20 * 1,01
        - Fechamento atual > MM20
        - Fechamento atual > Máxima do candle anterior
        - Volume atual >= Média de volume dos últimos 20 pregões
        """
        if idx < 20:
            return self._resultado('Pullback MM20', False)
        
        df = self.dados
        indicadores = self.indicadores
        
        minima_atual = df['Low'].iloc[idx]
        fechamento_atual = df['Close'].iloc[idx]
        maxima_anterior = df['High'].iloc[idx - 1]
        volume_atual = df['Volume'].iloc[idx]
        
        mm20 = indicadores['MM20'].iloc[idx]
        volmean20 = indicadores['VOLMEAN20'].iloc[idx]
        
        if pd.isna(mm20) or pd.isna(volmean20):
            return self._resultado('Pullback MM20', False)
        
        criterio1 = minima_atual <= mm20 * 1.01
        criterio2 = fechamento_atual > mm20
        criterio3 = fechamento_atual > maxima_anterior
        criterio4 = volume_atual >= volmean20
        
        ativo = criterio1 and criterio2 and criterio3 and criterio4
        
        detalhes = {
            'criterio_minima_mm20': bool(criterio1),
            'criterio_fechamento_mm20': bool(criterio2),
            'criterio_fechamento_max_ant': bool(criterio3),
            'criterio_volume': bool(criterio4),
        }
        
        return self._resultado('Pullback MM20', ativo, detalhes)
    
    def avaliar_gatilho_rompimento(self, idx: int) -> dict:
        """
        Gatilho B: Rompimento de Topo
        
        Critérios:
        - Fechamento atual >= Topo20 * 1,01
        - Volume atual >= Média de volume dos últimos 20 pregões * 1,20
        """
        if idx < 20:
            return self._resultado('Rompimento de Topo', False)
        
        df = self.dados
        indicadores = self.indicadores
        
        fechamento_atual = df['Close'].iloc[idx]
        volume_atual = df['Volume'].iloc[idx]
        
        topo20 = indicadores['TOPO20'].iloc[idx]
        volmean20 = indicadores['VOLMEAN20'].iloc[idx]
        
        if pd.isna(topo20) or pd.isna(volmean20):
            return self._resultado('Rompimento de Topo', False)
        
        criterio1 = fechamento_atual >= topo20 * 1.01
        criterio2 = volume_atual >= volmean20 * 1.20
        
        ativo = criterio1 and criterio2
        
        detalhes = {
            'criterio_rompimento_topo': bool(criterio1),
            'criterio_volume_rompimento': bool(criterio2),
        }
        
        return self._resultado('Rompimento de Topo', ativo, detalhes)
    
    def avaliar_gatilhos(self, idx: int) -> dict:
        """
        Avalia todos os gatilhos de entrada.
        
        Returns:
            dict com resultados de cada gatilho
        """
        pullback = self.avaliar_gatilho_pullback(idx)
        rompimento = self.avaliar_gatilho_rompimento(idx)
        
        gatilho_ativo = pullback['ativo'] or rompimento['ativo']
        tipo_entrada = None
        if pullback['ativo']:
            tipo_entrada = 'Pullback MM20'
        elif rompimento['ativo']:
            tipo_entrada = 'Rompimento de Topo'
        
        return {
            'gatilho_ativo': gatilho_ativo,
            'tipo_entrada': tipo_entrada,
            'pullback': pullback,
            'rompimento': rompimento,
        }
    
    def _resultado(self, nome: str, ativo: bool, detalhes: dict = None) -> dict:
        return {
            'nome': nome,
            'ativo': ativo,
            'detalhes': detalhes or {}
        }