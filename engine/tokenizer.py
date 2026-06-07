"""
Tokenizador para a linguagem de fórmulas de sinais.

Converte uma string de fórmula em tokens para processamento pelo parser.
"""
import re
from typing import List, Tuple


class Token:
    """Representa um token individual."""
    def __init__(self, tipo: str, valor: str, posicao: int = 0):
        self.tipo = tipo      # VARIAVEL, NUMERO, OPERADOR, PARENTESE, COMPARADOR, LOGICO
        self.valor = valor    # O texto do token
        self.posicao = posicao  # Posição na string original

    def __repr__(self):
        return f"Token({self.tipo}, '{self.valor}')"


# Padrões de tokenização em ordem de prioridade
TOKEN_PATTERNS = [
    ('NUMERO', r'\d+\.?\d*'),
    ('VARIAVEL', r'[A-Z_]+\[\d+\](?:\.SHIFT\[\d+\])?'),  # AC[20], MM[20].SHIFT[5]
    ('VARIAVEL', r'[A-Z_]+'),  # ADX, IFR, GAP, etc.
    ('LOGICO', r'&&|\|\|'),
    ('COMPARADOR', r'>=|<=|!=|==|>|<'),
    ('PARENTESE', r'[()]'),
    ('OPERADOR', r'[+\-*/]'),
    ('VIRGULA', r','),
    ('ESPACO', r'\s+'),
]


def tokenizar(expressao: str) -> List[Token]:
    """
    Tokeniza uma expressão de fórmula.
    
    Args:
        expressao: String contendo a fórmula (ex: "AC[10] > AC[20] && H[0] == HH[20]")
    
    Returns:
        Lista de tokens
    """
    tokens = []
    pos = 0
    
    while pos < len(expressao):
        melhor_match = None
        melhor_tipo = None
        melhor_tamanho = 0
        
        for tipo, padrao in TOKEN_PATTERNS:
            regex = re.compile(padrao)
            match = regex.match(expressao, pos)
            if match and match.end() - pos > melhor_tamanho:
                melhor_match = match
                melhor_tipo = tipo
                melhor_tamanho = match.end() - pos
        
        if not melhor_match:
            raise SyntaxError(
                f"Token não reconhecido na posição {pos}: "
                f"'{expressao[pos:pos+20]}...'"
            )
        
        valor = melhor_match.group()
        
        # Ignorar espaços
        if melhor_tipo != 'ESPACO':
            tokens.append(Token(melhor_tipo, valor, pos))
        
        pos = melhor_match.end()
    
    return tokens


def tokenizar_com_validacao(expressao: str) -> List[Token]:
    """
    Tokeniza e valida a expressão, retornando erros claros.
    
    Args:
        expressao: Fórmula a ser tokenizada
    
    Returns:
        Lista de tokens válidos
    
    Raises:
        SyntaxError: Se houver erro de sintaxe
    """
    expressao = expressao.strip()
    if not expressao:
        raise SyntaxError("Expressão vazia")
    
    tokens = tokenizar(expressao)
    
    if not tokens:
        raise SyntaxError("Expressão não contém tokens válidos")
    
    return tokens