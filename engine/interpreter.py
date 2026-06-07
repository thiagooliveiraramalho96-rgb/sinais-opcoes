"""
Interpretador/Avaliador da AST de fórmulas.

Avalia a AST contra dados reais de mercado (DataFrame).
"""
import pandas as pd
import numpy as np
from .parser import (
    ASTNode, NumeroNode, VariavelNode, VariavelIndexadaNode, OperadorBinarioNode
)


class Interpretador:
    """
    Avalia uma expressão AST contra um DataFrame de dados OHLCV.
    
    Os dados do DataFrame devem ter colunas: Open, High, Low, Close, Volume
    """
    
    def __init__(self, dados: pd.DataFrame, indicadores: dict = None):
        """
        Args:
            dados: DataFrame com colunas Open, High, Low, Close, Volume
            indicadores: Dicionário com indicadores pré-calculados (opcional)
                         Ex: {'MM20': Series, 'ADX': Series, 'IFR': Series}
        """
        self.dados = dados
        self.indicadores = indicadores or {}
        self._preparar_variaveis()
    
    def _preparar_variaveis(self):
        """Prepara variáveis especiais como AC (Average Close)."""
        self._variaveis_especiais = {}
        
        # AC[N] - Average Close dos últimos N candles
        # (calculado sob demanda, mas registramos suporte)
    
    def _calcular_ac(self, n: int, idx: int) -> float:
        """Calcula Average Close dos últimos N candles até a posição idx."""
        if idx < n - 1:
            return np.nan
        return self.dados['Close'].iloc[idx - n + 1:idx + 1].mean()
    
    def _obter_valor(self, no: ASTNode, idx: int) -> float:
        """Obtém o valor numérico de um nó da AST."""
        
        if isinstance(no, NumeroNode):
            return no.valor
        
        elif isinstance(no, VariavelNode):
            nome = no.nome.upper()
            
            # Verificar indicadores primeiro
            if nome in self.indicadores:
                valor = self.indicadores[nome].iloc[idx]
                return float(valor) if not pd.isna(valor) else np.nan
            
            # Variáveis do dataframe
            mapa_colunas = {
                'OPEN': 'Open', 'HIGH': 'High', 'LOW': 'Low', 
                'CLOSE': 'Close', 'VOLUME': 'Volume',
                'H': 'High', 'L': 'Low', 'C': 'Close', 'O': 'Open', 'V': 'Volume',
                'GAP': None  # Tratamento especial
            }
            
            if nome == 'GAP':
                return self._calcular_gap(idx)
            
            if nome in mapa_colunas:
                col = mapa_colunas[nome]
                return float(self.dados[col].iloc[idx])
            
            raise ValueError(f"Variável desconhecida: {nome}")
        
        elif isinstance(no, VariavelIndexadaNode):
            return self._obter_valor_indexado(no, idx)
        
        elif isinstance(no, OperadorBinarioNode):
            return self._avaliar_operador(no, idx)
        
        raise ValueError(f"Nó desconhecido: {type(no)}")
    
    def _obter_valor_indexado(self, no: VariavelIndexadaNode, idx: int) -> float:
        """Obtém valor de variável indexada (ex: AC[20], H[0], HH[20])."""
        nome = no.nome.upper()
        indice = no.indice
        shift = no.shift if no.shift is not None else 0
        
        idx_alvo = idx - shift
        
        if idx_alvo < 0:
            return np.nan
        
        # AC[N] - Average Close
        if nome == 'AC':
            return self._calcular_ac(indice, idx_alvo)
        
        # HH[N] - Highest High dos últimos N candles
        if nome == 'HH':
            return self._calcular_hh(indice, idx_alvo)
        
        # LL[N] - Lowest Low dos últimos N candles
        if nome == 'LL':
            return self._calcular_ll(indice, idx_alvo)
        
        # MM[N] - Média Móvel de N períodos
        if nome == 'MM':
            return self._calcular_mm(indice, idx_alvo)
        
        # MAX[N] - Maior valor de N períodos
        if nome == 'MAX':
            return self._calcular_max(indice, idx_alvo)
        
        # MIN[N] - Menor valor de N períodos
        if nome == 'MIN':
            return self._calcular_min(indice, idx_alvo)
        
        # STD[N] - Desvio padrão de N períodos
        if nome == 'STD':
            return self._calcular_std(indice, idx_alvo)
        
        # VOLMEAN[N] - Média de volume dos últimos N
        if nome in ('VOLMEAN', 'VM'):
            if idx_alvo < indice - 1:
                return np.nan
            return self.dados['Volume'].iloc[idx_alvo - indice + 1:idx_alvo + 1].mean()
        
        # BODY - Tamanho do corpo do candle
        if nome == 'BODY':
            return abs(self.dados['Close'].iloc[idx_alvo] - self.dados['Open'].iloc[idx_alvo])
        
        # WICK - Sombra superior/inferior
        if nome == 'WICK':
            high = self.dados['High'].iloc[idx_alvo]
            low = self.dados['Low'].iloc[idx_alvo]
            close = self.dados['Close'].iloc[idx_alvo]
            open_p = self.dados['Open'].iloc[idx_alvo]
            body_top = max(close, open_p)
            body_bottom = min(close, open_p)
            return (high - body_top) + (body_bottom - low)
        
        # H[N], L[N], C[N], O[N], V[N] - candle específico
        if nome in ('H', 'HIGH'):
            col = 'High'
        elif nome in ('L', 'LOW'):
            col = 'Low'
        elif nome in ('C', 'CLOSE'):
            col = 'Close'
        elif nome in ('O', 'OPEN'):
            col = 'Open'
        elif nome in ('V', 'VOLUME'):
            col = 'Volume'
        else:
            raise ValueError(f"Variável indexada desconhecida: {nome}[{indice}]")
        
        return float(self.dados[col].iloc[idx_alvo])
    
    def _calcular_hh(self, n: int, idx: int) -> float:
        """Highest High dos últimos N candles."""
        if idx < n - 1:
            return np.nan
        return self.dados['High'].iloc[idx - n + 1:idx + 1].max()
    
    def _calcular_ll(self, n: int, idx: int) -> float:
        """Lowest Low dos últimos N candles."""
        if idx < n - 1:
            return np.nan
        return self.dados['Low'].iloc[idx - n + 1:idx + 1].min()
    
    def _calcular_mm(self, n: int, idx: int) -> float:
        """Média Móvel de N períodos."""
        if idx < n - 1:
            return np.nan
        return self.dados['Close'].iloc[idx - n + 1:idx + 1].mean()
    
    def _calcular_max(self, n: int, idx: int) -> float:
        """Maior valor de N períodos (fechamento)."""
        if idx < n - 1:
            return np.nan
        return self.dados['Close'].iloc[idx - n + 1:idx + 1].max()
    
    def _calcular_min(self, n: int, idx: int) -> float:
        """Menor valor de N períodos (fechamento)."""
        if idx < n - 1:
            return np.nan
        return self.dados['Close'].iloc[idx - n + 1:idx + 1].min()
    
    def _calcular_std(self, n: int, idx: int) -> float:
        """Desvio padrão de N períodos (fechamento)."""
        if idx < n - 1:
            return np.nan
        return self.dados['Close'].iloc[idx - n + 1:idx + 1].std()
    
    def _calcular_gap(self, idx: int) -> float:
        """Calcula o gap percentual do candle atual."""
        if idx < 1:
            return 0.0
        low = self.dados['Low'].iloc[idx]
        prev_close = self.dados['Close'].iloc[idx - 1]
        if prev_close == 0:
            return 0.0
        gap = (low - prev_close) / prev_close * 100
        return gap
    
    def _avaliar_operador(self, no: OperadorBinarioNode, idx: int) -> float:
        """Avalia um operador binário."""
        esquerda = self._obter_valor(no.esquerda, idx)
        direita = self._obter_valor(no.direita, idx)
        
        # Operadores lógicos
        if no.operador == '&&':
            return 1.0 if esquerda and direita else 0.0
        elif no.operador == '||':
            return 1.0 if esquerda or direita else 0.0
        
        # Operadores de comparação
        elif no.operador == '>':
            return 1.0 if esquerda > direita else 0.0
        elif no.operador == '<':
            return 1.0 if esquerda < direita else 0.0
        elif no.operador == '>=':
            return 1.0 if esquerda >= direita else 0.0
        elif no.operador == '<=':
            return 1.0 if esquerda <= direita else 0.0
        elif no.operador == '==':
            return 1.0 if esquerda == direita else 0.0
        elif no.operador == '!=':
            return 1.0 if esquerda != direita else 0.0
        
        # Operadores aritméticos
        elif no.operador == '+':
            return esquerda + direita
        elif no.operador == '-':
            return esquerda - direita
        elif no.operador == '*':
            return esquerda * direita
        elif no.operador == '/':
            if direita == 0:
                return np.inf
            return esquerda / direita
        
        raise ValueError(f"Operador desconhecido: {no.operador}")
    
    def avaliar(self, ast: ASTNode, idx: int) -> bool:
        """
        Avalia a AST em uma posição específica do DataFrame.
        
        Args:
            ast: Raiz da AST gerada pelo parser
            idx: Índice da linha no DataFrame (0-based)
        
        Returns:
            True se a expressão for verdadeira, False caso contrário
        """
        if idx < 0 or idx >= len(self.dados):
            return False
        
        try:
            resultado = self._obter_valor(ast, idx)
            return bool(resultado)
        except (ValueError, KeyError, IndexError) as e:
            return False
    
    def avaliar_serie(self, ast: ASTNode) -> pd.Series:
        """
        Avalia a AST para todas as posições do DataFrame.
        
        Returns:
            Series booleana com resultados
        """
        resultados = []
        for idx in range(len(self.dados)):
            resultados.append(self.avaliar(ast, idx))
        return pd.Series(resultados, index=self.dados.index)