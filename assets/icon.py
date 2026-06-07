"""
Gerador de ícone simples para o app.
Execute: python assets/icon.py
"""
from PIL import Image, ImageDraw, ImageFont
import os

def gerar_icone():
    """Gera um ícone simples de 512x512 px."""
    img = Image.new('RGBA', (512, 512), (27, 94, 32, 255))  # Verde escuro
    draw = ImageDraw.Draw(img)
    
    # Desenhar um gráfico de linha simplificado
    pontos = [(100, 400), (180, 350), (260, 370), (340, 280), (420, 320)]
    draw.line(pontos, fill=(255, 255, 255, 200), width=8)
    
    # Círculo no último ponto
    draw.ellipse([412, 312, 428, 328], fill=(0, 255, 0, 255))
    
    # Seta para cima
    draw.polygon([(420, 280), (440, 320), (400, 320)], fill=(0, 255, 0, 255))
    
    # Texto "S" estilizado
    try:
        font = ImageFont.truetype("arial.ttf", 120)
    except:
        font = ImageFont.load_default()
    
    draw.text((200, 100), "S", fill=(255, 255, 255, 255), font=font)
    draw.text((200, 200), "O", fill=(255, 255, 255, 200), font=font)
    
    # Salvar
    caminho = os.path.join(os.path.dirname(__file__), 'icon.png')
    img.save(caminho, 'PNG')
    print(f"Ícone gerado: {caminho}")
    
    # Gerar splash
    splash = Image.new('RGBA', (256, 256), (27, 94, 32, 255))
    draw_splash = ImageDraw.Draw(splash)
    draw_splash.text((50, 80), "Sinais", fill=(255, 255, 255), font=font)
    draw_splash.text((50, 160), "Opções", fill=(255, 255, 255, 200), font=font)
    splash.save(os.path.join(os.path.dirname(__file__), 'splash.png'), 'PNG')
    print(f"Splash gerado: {os.path.join(os.path.dirname(__file__), 'splash.png')}")

if __name__ == '__main__':
    gerar_icone()