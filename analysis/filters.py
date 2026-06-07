"""
Filtros obrigatórios para geração de sinais.
"""
import pandas as pd
import numpy as np
from .indicators import IndicatorCalculator


class SignalFilters:
    """
    Aplica os filtros obrigatórios definidos na estratégia.
    """
    
    def __init__(self, dados: pd.DataFrame, indicadores: dict):
        """
        Args:
            dados: DataFrame OHLCV
            indicadores: Dict com indicadores calculados
        """
        self.dados = dados
        self.indicadores = indicadores
    
    def aplicar_filtros(self, idx: int) -> dict:
        """
        Aplica todos os filtros obrigatórios em um índice específico.
        
        Returns:
            dict com resultados de cada filtro e status geral
        """
        if idx < 200:  # Precisamos de pelo menos 200 candles para MM200
            return self._resultado_falso("Dados insuficientes (mínimo 200 candles)")
        
        resultados = {}
        
        resultados['preco_acima_mm200'] = self._preco_acima_mm200(idx)
        resultados['preco_acima_mm50'] = self._preco_acima_mm50(idx)
        resultados['mm20_acima_mm50'] = self._mm20_acima_mm50(idx)
        resultados['mm50_subindo'] = self._mm50_subindo(idx)
        resultados['adx_maior_25'] = self._adx_maior_25(idx)
        resultados['adx_subindo'] = self._adx_subindo(idx)
        resultados['ifr_45_75'] = self._ifr_entre_45_75(idx)
        resultados['dist_mm20_8p'] = self._distancia_mm20_ate_8(idx)
        resultados['sem_alta_5p'] = self._sem_alta_superior_5p(idx)
        resultados['sem_gap_3p'] = self._sem_gap_superior_3p(idx)
        
        # Verificar se todos os filtros passaram
        todos_ok = all(resultados.values()) if resultados else False
        
        return {
            'aprovado': todos_ok,
            'detalhes': resultados,
            'mensagem': 'Todos os filtros aprovados' if todos_ok else self._gerar_mensagem_erro(resultados)
        }
    
    def _resultado_falso(self, motivo: str) -> dict:
        return {
            'aprovado': False,
            'detalhes': {},
            'mensagem': motivo
        }
    
    def _preco_acima_mm200(self, idx: int) -> bool:
        """Preço atual > MM200"""
        preco = self.dados['Close'].iloc[idx]
        mm200 = self.indicadores['MM200'].iloc[idx]
        if pd.isna(mm200):
            return False
        return preco > mm200
    
    def _preco_acima_mm50(self, idx: int) -> bool:
        """Preço atual > MM50"""
        preco = self.dados['Close'].iloc[idx]
        mm50 = self.indicadores['MM50'].iloc[idx]
        if pd.isna(mm50):
            return False
        return preco > mm50
    
    def _mm20_acima_mm50(self, idx: int) -> bool:
        """MM20 > MM50"""
        mm20 = self.indicadores['MM20'].iloc[idx]
        mm50 = self.indicadores['MM50'].iloc[idx]
        if pd.isna(mm20) or pd.isna(mm50):
            return False
        return mm20 > mm50
    
    def _mm50_subindo(self, idx: int) -> bool:
        """MM50 atual > MM50 de 5 candles atrás"""
        if idx < 5:
            return False
        mm50_atual = self.indicadores['MM50'].iloc[idx]
        mm50_5atras = self.indicadores['MM50'].iloc[idx - 5]
        if pd.isna(mm50_atual) or pd.isna(mm50_5atras):
            return False
        return mm50_atual > mm50_5atras
    
    def _adx_maior_25(self, idx: int) -> bool:
        """ADX(14) > 25"""
        adx = self.indicadores['ADX'].iloc[idx]
        if pd.isna(adx):
            return False
        return adx > 25
    
    def _adx_subindo(self, idx: int) -> bool:
        """ADX atual > ADX de 5 candles atrás"""
        if idx < 5:
            return False
        adx_atual = self.indicadores['ADX'].iloc[idx]
        adx_5atras = self.indicadores['ADX'].iloc[idx - 5]
        if pd.isna(adx_atual) or pd.isna(adx_5atras):
            return False
        return adx_atual > adx_5atras
    
    def _ifr_entre_45_75(self, idx: int) -> bool:
        """45 <= IFR(14) <= 75"""
        ifr = self.indicadores['IFR'].iloc[idx]
        if pd.isna(ifr):
            return False
        return 45 <= ifr <= 75
    
    def _distancia_mm20_ate_8(self, idx: int) -> bool:
        """Distância entre preço atual e MM20 <= 8%"""
        preco = self.dados['Close'].iloc[idx]
        mm20 = self.indicadores['MM20'].iloc[idx]
        if pd.isna(mm20) or mm20 == 0:
            return False
        distancia = abs(preco - mm20) / mm20 * 100
        return distancia <= 8.0
    
    def _sem_alta_superior_5p(self, idx: int) -> bool:
        """Nenhum candle dos últimos 2 pregões teve alta superior a 5%"""
        if idx < 2:
            return False
        for i in range(idx - 1, idx + 1):
            if i < 0 or i >= len(self.dados):
                continue
            ret = self.indicadores['RET'].iloc[i]
            if not pd.isna(ret) and ret > 5.0:
                return False
        return True
    
    def _sem_gap_superior_3p(self, idx: int) -> bool:
        """Nenhum gap de alta superior a 3% nos últimos 2 pregões"""
        if idx < 2:
            return False
        for i in range(idx - 1, idx + 1):
            if i < 0 or i >= len(self.dados):
                continue
            gap = self.indicadores['GAP'].iloc[i]
            if not pd.isna(gap) and gap > 3.0:
                return False
        return True
    
    def _gerar_mensagem_erro(self, resultados: dict) -> str:
        """Gera mensagem com quais filtros falharam."""
        falhas = []
        mapa_nomes = {
            'preco_acima_mm200': 'Preço > MM200',
            'preco_acima_mm50': 'Preço > MM50',
            'mm20_acima_mm50': 'MM20 > MM50',
            'mm50_subindo': 'MM50 subindo',
            'adx_maior_25': 'ADX > 25',
            'adx_subindo': 'ADX subindo',
            'ifr_45_75': 'IFR entre 45-75',
            'dist_mm20_8p': 'Distância MM20 ≤ 8%',
            'sem_alta_5p': 'Sem alta > 5% (2 pregões)',
            'sem_gap_3p': 'Sem gap > 3% (2 pregões)',
        }
        for chave, aprovado in resultados.items():
            if not aprovado:
                nome = mapa_nomes.get(chave, chave)
                falhas.append(nome)
        return f"Filtros reprovados: {', '.join(falhas)}"