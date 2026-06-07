"""
Validador de fórmulas - verifica sintaxe e lista variáveis usadas.
"""
from typing import List, Set, Tuple
from .parser import parse, ASTNode, VariavelNode, VariavelIndexadaNode, OperadorBinarioNode, NumeroNode


def validar_formula(expressao: str) -> Tuple[bool, str, ASTNode]:
    """
    Valida uma expressão de fórmula.
    
    Args:
        expressao: String com a fórmula
    
    Returns:
        (valido, mensagem_erro, ast)
    """
    try:
        ast = parse(expressao)
        return True, "Fórmula válida", ast
    except SyntaxError as e:
        return False, f"Erro de sintaxe: {str(e)}", None
    except Exception as e:
        return False, f"Erro inesperado: {str(e)}", None


def obter_variaveis_da_formula(ast: ASTNode) -> Set[str]:
    """
    Extrai todas as variáveis usadas em uma AST.
    
    Returns:
        Set com nomes das variáveis
    """
    variaveis = set()
    
    def _visitar(no: ASTNode):
        if isinstance(no, VariavelNode):
            variaveis.add(no.nome)
        elif isinstance(no, VariavelIndexadaNode):
            variaveis.add(f"{no.nome}[{no.indice}]")
            if no.shift is not None:
                variaveis.add(f"SHIFT[{no.shift}]")
        elif isinstance(no, OperadorBinarioNode):
            _visitar(no.esquerda)
            _visitar(no.direita)
        # NumeroNode não contribui variáveis
    
    _visitar(ast)
    return variaveis


def obter_variaveis_da_string(expressao: str) -> Set[str]:
    """
    Valida e extrai variáveis de uma expressão.
    
    Returns:
        Set com nomes das variáveis
    """
    valido, msg, ast = validar_formula(expressao)
    if not valido:
        raise SyntaxError(msg)
    return obter_variaveis_da_formula(ast)