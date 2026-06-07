"""
Parser para a linguagem de fórmulas de sinais.

Converte uma lista de tokens em uma Árvore Sintática Abstrata (AST).
"""
from typing import List, Union, Optional
from .tokenizer import Token


class ASTNode:
    """Nó base da AST."""
    pass


class NumeroNode(ASTNode):
    """Nó para número literal."""
    def __init__(self, valor: float):
        self.valor = valor
    
    def __repr__(self):
        return f"Numero({self.valor})"


class VariavelNode(ASTNode):
    """Nó para variável simples (ex: ADX, IFR, GAP)."""
    def __init__(self, nome: str):
        self.nome = nome
    
    def __repr__(self):
        return f"Variavel({self.nome})"


class VariavelIndexadaNode(ASTNode):
    """Nó para variável indexada (ex: AC[20], H[0])."""
    def __init__(self, nome: str, indice: int, shift: Optional[int] = None):
        self.nome = nome
        self.indice = indice
        self.shift = shift  # SHIFT opcional
    
    def __repr__(self):
        base = f"{self.nome}[{self.indice}]"
        if self.shift is not None:
            base += f".SHIFT[{self.shift}]"
        return base


class OperadorBinarioNode(ASTNode):
    """Nó para operação binária (ex: >, <, +, -, &&, ||)."""
    def __init__(self, operador: str, esquerda: ASTNode, direita: ASTNode):
        self.operador = operador
        self.esquerda = esquerda
        self.direita = direita
    
    def __repr__(self):
        return f"({self.esquerda} {self.operador} {self.direita})"


class Parser:
    """
    Parser descendente recursivo para fórmulas.
    
    Gramática:
        expressao      → expressao_logica
        expressao_logica → expressao_comparacao (('&&' | '||') expressao_comparacao)*
        expressao_comparacao → expressao_aritmetica (('>' | '<' | '>=' | '<=' | '==' | '!=') expressao_aritmetica)*
        expressao_aritmetica → termo (('+' | '-') termo)*
        termo          → fator (('*' | '/') fator)*
        fator          → NUMERO | VARIAVEL | '(' expressao ')'
    """
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
    
    def parser_expressao(self) -> ASTNode:
        """Ponto de entrada: expressao → expressao_logica"""
        return self._parser_expressao_logica()
    
    def _parser_expressao_logica(self) -> ASTNode:
        """expressao_logica → expressao_comparacao (('&&' | '||') expressao_comparacao)*"""
        esquerda = self._parser_expressao_comparacao()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos].tipo == 'LOGICO':
            operador = self.tokens[self.pos].valor
            self.pos += 1
            direita = self._parser_expressao_comparacao()
            esquerda = OperadorBinarioNode(operador, esquerda, direita)
        
        return esquerda
    
    def _parser_expressao_comparacao(self) -> ASTNode:
        """expressao_comparacao → expressao_aritmetica (COMPARADOR expressao_aritmetica)*"""
        esquerda = self._parser_expressao_aritmetica()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos].tipo == 'COMPARADOR':
            operador = self.tokens[self.pos].valor
            self.pos += 1
            direita = self._parser_expressao_aritmetica()
            esquerda = OperadorBinarioNode(operador, esquerda, direita)
        
        return esquerda
    
    def _parser_expressao_aritmetica(self) -> ASTNode:
        """expressao_aritmetica → termo (('+' | '-') termo)*"""
        esquerda = self._parser_termo()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos].tipo == 'OPERADOR' and self.tokens[self.pos].valor in ('+', '-'):
            operador = self.tokens[self.pos].valor
            self.pos += 1
            direita = self._parser_termo()
            esquerda = OperadorBinarioNode(operador, esquerda, direita)
        
        return esquerda
    
    def _parser_termo(self) -> ASTNode:
        """termo → fator (('*' | '/') fator)*"""
        esquerda = self._parser_fator()
        
        while self.pos < len(self.tokens) and self.tokens[self.pos].tipo == 'OPERADOR' and self.tokens[self.pos].valor in ('*', '/'):
            operador = self.tokens[self.pos].valor
            self.pos += 1
            direita = self._parser_fator()
            esquerda = OperadorBinarioNode(operador, esquerda, direita)
        
        return esquerda
    
    def _parser_fator(self) -> ASTNode:
        """fator → NUMERO | VARIAVEL | '(' expressao ')'"""
        if self.pos >= len(self.tokens):
            raise SyntaxError("Expressão incompleta - esperava token")
        
        token = self.tokens[self.pos]
        
        if token.tipo == 'NUMERO':
            self.pos += 1
            try:
                return NumeroNode(float(token.valor))
            except ValueError:
                raise SyntaxError(f"Número inválido: '{token.valor}'")
        
        elif token.tipo == 'VARIAVEL':
            self.pos += 1
            return self._parser_variavel(token)
        
        elif token.tipo == 'PARENTESE' and token.valor == '(':
            self.pos += 1
            no = self._parser_expressao_logica()
            if self.pos >= len(self.tokens) or self.tokens[self.pos].valor != ')':
                raise SyntaxError("Parêntese não fechado")
            self.pos += 1
            return no
        
        else:
            raise SyntaxError(
                f"Token inesperado na posição {token.posicao}: "
                f"'{token.valor}' (tipo: {token.tipo})"
            )
    
    def _parser_variavel(self, token: Token) -> ASTNode:
        """Processa uma variável que pode ser indexada ou simples."""
        valor = token.valor
        
        # Verifica se é variável indexada: AC[20]
        if '[' in valor:
            nome = valor.split('[')[0]
            resto = valor.split('[')[1]  # "20]" ou "20].SHIFT[5]"
            
            if '].SHIFT[' in resto:
                indice_str, shift_str = resto.split('].SHIFT[')
                indice = int(indice_str)
                shift = int(shift_str.rstrip(']'))
                return VariavelIndexadaNode(nome, indice, shift)
            else:
                indice = int(resto.rstrip(']'))
                return VariavelIndexadaNode(nome, indice)
        
        # Variável simples: ADX, IFR, etc
        return VariavelNode(valor)


def parse(expressao: str) -> ASTNode:
    """
    Função de conveniência: tokeniza e parseia uma expressão.
    
    Args:
        expressao: String com a fórmula
    
    Returns:
        Nó raiz da AST
    
    Raises:
        SyntaxError: Se houver erro de sintaxe
    """
    from .tokenizer import tokenizar_com_validacao
    tokens = tokenizar_com_validacao(expressao)
    parser = Parser(tokens)
    ast = parser.parser_expressao()
    
    if parser.pos < len(tokens):
        raise SyntaxError(
            f"Tokens não processados após posição {parser.pos}: "
            f"'{' '.join(t.valor for t in tokens[parser.pos:])}'"
        )
    
    return ast