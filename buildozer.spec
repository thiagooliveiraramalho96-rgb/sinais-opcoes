[app]

# Nome do aplicativo
title = Sinais Opções B3

# Nome do pacote (deve ser único)
package.name = sinaisopcoes

# Domínio do pacote
package.domain = org.trade.b3

# Versão
version = 1.0.0

# Código de versão (número inteiro incremental)
version.code = 1

# Arquivo principal
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,otf,txt

# Arquivos a serem incluídos
source.exclude_exts = spec

# Ícone (necessário gerar um)
icon = assets/icon.png

# Permissões do Android
android.permissions = INTERNET, ACCESS_NETWORK_STATE, VIBRATE, POST_NOTIFICATIONS, RECEIVE_BOOT_COMPLETED, WAKE_LOCK, FOREGROUND_SERVICE

# API Android alvo
android.api = 33
android.minapi = 24
android.ndk = 28c
android.ndk_path = 
android.sdk_path = 
android.build_tools = 33.0.2

# Requisitos (bibliotecas Python)
#requirements = python3,kivy==2.3.1,kivymd==1.2.0,pandas==2.0.3,numpy==1.24.3,yfinance==0.2.18,pandas_ta==0.3.14b0,matplotlib==3.7.1,plyer==2.1.0,schedule==1.2.0,scipy==1.10.1,requests==2.31.0
requirements = python3,kivy==2.3.1,kivymd==1.2.0,requests,plyer


# Orientação
orientation = portrait

# Modo escuro nativo
android.night_mode = yes

# Argumentos para o Python
osx.python_version = 3.12

# Tema (Material Design)
presplash_color = #1B5E20
android.window_splashscreen = assets/splash.png

# Storage
android.storage_backend = internal
android.enable_androidx = True

# Metadados
author = Sinais Opcoes B3
description = Aplicativo para geração de sinais de compra de opções CALL ATM
keywords = opções, sinais, b3, análise técnica

[buildozer]

# Estratégia de log
log_level = 2

# Tentar usar docker
docker = 0

# Warnings
warn_on_root = 1

# Arquivo de saída
export_filename = SinaisOpcoesB3

# Compressão
android.whitelist =