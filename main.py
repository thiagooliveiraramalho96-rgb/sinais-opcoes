"""
Sinais Opções B3 - Aplicativo de Sinais para Opções CALL ATM

Ponto de entrada principal do aplicativo.
Execute com: python main.py
"""
import os
import sys
import platform

# Fix para Windows: desativar toque redirecionado
if platform.system() == 'Windows':
    os.environ['KIVY_NO_CONSOLELOG'] = '1'

# Configurar PATH para importações
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importar a aplicação
from ui.app import SinaisOpcoesApp


def main():
    """Ponto de entrada principal."""
    print("=" * 50)
    print("  📊 SINAIS OPÇÕES B3 v1.0")
    print("  Aplicativo de Sinais para Opções CALL ATM")
    print("=" * 50)
    print("  Iniciando...")
    
    try:
        app = SinaisOpcoesApp()
        app.run()
    except KeyboardInterrupt:
        print("\n[APP] Encerrado pelo usuário")
    except Exception as e:
        print(f"\n[ERRO] {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")


if __name__ == '__main__':
    main()