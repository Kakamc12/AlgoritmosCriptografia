# Laboratório de cifras

Interface web (HTML/CSS/JS) com backend em Python (Flask) para testar as cifras
das bibliotecas `criptomat.py` e `cifras.py`.

## Estrutura

```
projeto_cifras/
├── app.py            servidor Flask (catálogo de cifras + API)
├── criptomat.py      biblioteca de teoria dos números
├── cifras.py         biblioteca de cifras (usa a criptomat)
├── requirements.txt
├── templates/
│   └── index.html    página principal
└── static/
    ├── style.css
    └── script.js
```

## Como rodar

```bash
# 1. (opcional) ambiente virtual
python -m venv venv
venv\Scripts\activate          # Windows
source venv/bin/activate       # Linux/macOS

# 2. instalar dependência
pip install -r requirements.txt

# 3. iniciar o servidor
python app.py
```

Abra **http://127.0.0.1:5000** no navegador.

## Como usar

1. Escolha a cifra na lista à esquerda.
2. Escolha a operação (cifrar, decifrar, força bruta etc.).
3. Preencha os campos e clique no botão (ou use Ctrl + Enter).
4. O resultado aparece no quadro âmbar. "Usar como entrada" leva o resultado
   para o campo de texto e alterna entre cifrar e decifrar, útil para conferir
   a ida e volta.

Nas cifras de fluxo (LFSR e RC4) o texto cifrado é mostrado em hexadecimal, e é
esse hexadecimal que deve ser colado na hora de decifrar.

## Como adicionar uma nova cifra

1. Escreva a função em `cifras.py`.
2. Em `app.py`, adicione uma entrada em `CIFRAS` (campos e operações que a
   interface deve mostrar) e uma em `EXECUTORES` (o que chamar). A página
   se monta sozinha a partir desse catálogo.

## Observação

As cifras são para estudo e não devem proteger dados reais. As fontes IBM Plex
são carregadas do Google Fonts; sem internet, o navegador usa fontes do sistema.
