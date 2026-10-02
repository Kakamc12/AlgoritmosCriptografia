# -*- coding: utf-8 -*-
"""
Laboratório de cifras: servidor Flask.

Rotas:
    GET  /               página principal
    GET  /api/cifras     catálogo de cifras (campos e operações de cada uma)
    POST /api/executar   executa uma operação e devolve o resultado em JSON

Para rodar:
    python app.py
e abra http://127.0.0.1:5000 no navegador.
"""

from flask import Flask, jsonify, render_template, request

import cifras

app = Flask(__name__)

LIMITE_TEXTO = 20_000      # caracteres
LIMITE_MATRIZ = 6          # ordem máxima da matriz de Hill
LIMITE_BYTES_FLUXO = 100_000
LIMITE_TAMANHO_LFSR = 128  # bits


# ---------------------------------------------------------------------------
# Catálogo: descreve o que a interface deve mostrar para cada cifra
# ---------------------------------------------------------------------------
def _op(id, rotulo, acao):
    """Operação: `rotulo` aparece no seletor, `acao` no texto do botão."""
    return {"id": id, "rotulo": rotulo, "acao": acao}


def _campo(id, rotulo, tipo="text", padrao="", ajuda="", ops=None,
           rotulos=None, placeholder=""):
    """
    Campo de entrada.
    ops     : operações em que o campo aparece (None = todas)
    rotulos : {operacao: rótulo alternativo}
    tipo    : "text", "textarea" ou "number"
    """
    return {
        "id": id, "rotulo": rotulo, "tipo": tipo, "padrao": padrao,
        "ajuda": ajuda, "ops": ops, "rotulos": rotulos or {},
        "placeholder": placeholder,
    }


CIFRAS = [
    {
        "id": "cesar",
        "nome": "César",
        "descricao": "Desloca cada letra um número fixo de posições no "
                     "alfabeto: C = (P + chave) mod 26.",
        "operacoes": [
            _op("cifrar", "Cifrar", "Cifrar texto"),
            _op("decifrar", "Decifrar", "Decifrar texto"),
            _op("forca_bruta", "Força bruta", "Tentar as 26 chaves"),
        ],
        "campos": [
            _campo("texto", "Texto", "textarea", "Ataque ao amanhecer",
                   rotulos={"decifrar": "Texto cifrado",
                            "forca_bruta": "Texto cifrado"}),
            _campo("chave", "Chave (deslocamento)", "number", "3",
                   "Número inteiro; 3 troca A por D.",
                   ops=["cifrar", "decifrar"]),
        ],
    },
    {
        "id": "substituicao",
        "nome": "Substituição",
        "descricao": "Cada letra do alfabeto é trocada pela letra que ocupa "
                     "a mesma posição na chave, uma permutação de A-Z.",
        "operacoes": [
            _op("cifrar", "Cifrar", "Cifrar texto"),
            _op("decifrar", "Decifrar", "Decifrar texto"),
            _op("gerar_chave", "Gerar chave", "Gerar chave aleatória"),
        ],
        "campos": [
            _campo("texto", "Texto", "textarea", "Ola, mundo!",
                   rotulos={"decifrar": "Texto cifrado"},
                   ops=["cifrar", "decifrar"]),
            _campo("chave", "Chave (26 letras sem repetir)", "text",
                   "QWERTYUIOPASDFGHJKLZXCVBNM",
                   "A primeira letra substitui o A, a segunda o B, e assim "
                   "por diante.",
                   ops=["cifrar", "decifrar"]),
        ],
    },
    {
        "id": "afim",
        "nome": "Afim",
        "descricao": "Combina multiplicação e soma: C = (a·P + b) mod 26. "
                     "O valor de a precisa ser coprimo com 26.",
        "operacoes": [
            _op("cifrar", "Cifrar", "Cifrar texto"),
            _op("decifrar", "Decifrar", "Decifrar texto"),
        ],
        "campos": [
            _campo("texto", "Texto", "textarea", "AFFINE CIPHER",
                   rotulos={"decifrar": "Texto cifrado"}),
            _campo("a", "Valor de a", "number", "5",
                   "Valores válidos: 1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25."),
            _campo("b", "Valor de b", "number", "8"),
        ],
    },
    {
        "id": "vigenere",
        "nome": "Vigenère",
        "descricao": "Usa uma palavra-chave: cada letra do texto é deslocada "
                     "pela letra correspondente da chave, que se repete.",
        "operacoes": [
            _op("cifrar", "Cifrar", "Cifrar texto"),
            _op("decifrar", "Decifrar", "Decifrar texto"),
        ],
        "campos": [
            _campo("texto", "Texto", "textarea", "ATTACK AT DAWN",
                   rotulos={"decifrar": "Texto cifrado"}),
            _campo("chave", "Palavra-chave", "text", "LEMON",
                   "Apenas letras de A a Z."),
        ],
    },
    {
        "id": "hill",
        "nome": "Hill",
        "descricao": "Cifra blocos de letras multiplicando por uma matriz "
                     "quadrada módulo 26. O determinante da matriz precisa "
                     "ser coprimo com 26.",
        "operacoes": [
            _op("cifrar", "Cifrar", "Cifrar texto"),
            _op("decifrar", "Decifrar", "Decifrar texto"),
            _op("matriz_inversa", "Matriz inversa", "Calcular matriz inversa"),
        ],
        "campos": [
            _campo("texto", "Texto", "textarea", "ACT",
                   "Só as letras são usadas; o último bloco é completado "
                   "com X.",
                   rotulos={"decifrar": "Texto cifrado"},
                   ops=["cifrar", "decifrar"]),
            _campo("matriz", "Matriz-chave", "textarea",
                   "6 24 1\n13 16 10\n20 17 15",
                   "Uma linha por linha da matriz, números separados por "
                   "espaço."),
        ],
    },
    {
        "id": "transposicao",
        "nome": "Transposição",
        "descricao": "Escreve o texto em linhas sob a palavra-chave e lê as "
                     "colunas na ordem alfabética das letras da chave. "
                     "Nenhuma letra muda, só a posição.",
        "operacoes": [
            _op("cifrar", "Cifrar", "Cifrar texto"),
            _op("decifrar", "Decifrar", "Decifrar texto"),
        ],
        "campos": [
            _campo("texto", "Texto", "textarea", "Ataque ao amanhecer",
                   rotulos={"decifrar": "Texto cifrado"}),
            _campo("chave", "Palavra-chave", "text", "ZEBRA",
                   "Cada letra é uma coluna; a ordem alfabética define a "
                   "leitura."),
        ],
    },
    {
        "id": "lfsr",
        "nome": "Fluxo: LFSR",
        "descricao": "Um registrador de deslocamento gera bytes pseudoaleatórios "
                     "que são combinados com o texto por XOR. A mesma semente "
                     "cifra e decifra.",
        "operacoes": [
            _op("cifrar", "Cifrar", "Cifrar texto"),
            _op("decifrar", "Decifrar", "Decifrar texto"),
            _op("gerar_fluxo", "Gerar fluxo", "Gerar bytes do fluxo"),
        ],
        "campos": [
            _campo("texto", "Texto", "textarea", "Ola mundo",
                   "Na decifragem, cole o resultado em hexadecimal.",
                   rotulos={"decifrar": "Texto cifrado (hexadecimal)"},
                   ops=["cifrar", "decifrar"]),
            _campo("semente", "Semente", "text", "0xACE1",
                   "Inteiro diferente de zero; aceita decimal ou hexadecimal (utilize prefixo 0x, ex.: 0xACE1).",
                   ),
            _campo("taps", "Taps", "text", "0,2,3,5",
                   "Posições dos bits usados na realimentação (0 é o menos "
                   "significativo)."),
            _campo("tamanho", "Tamanho do registrador (bits)", "number", "16"),
            _campo("n_bytes", "Quantidade de bytes", "number", "8",
                   ops=["gerar_fluxo"]),
        ],
    },
    {
        "id": "rc4",
        "nome": "Fluxo: RC4",
        "descricao": "Cifra de fluxo clássica: a chave embaralha uma tabela "
                     "de 256 bytes que produz o fluxo combinado por XOR com "
                     "o texto.",
        "operacoes": [
            _op("cifrar", "Cifrar", "Cifrar texto"),
            _op("decifrar", "Decifrar", "Decifrar texto"),
        ],
        "campos": [
            _campo("texto", "Texto", "textarea", "Plaintext",
                   "Na decifragem, cole o resultado em hexadecimal.",
                   rotulos={"decifrar": "Texto cifrado (hexadecimal)"}),
            _campo("chave", "Chave", "text", "Key",
                   "Texto de 1 a 256 bytes."),
        ],
    },
]

CIFRAS_POR_ID = {c["id"]: c for c in CIFRAS}


# ---------------------------------------------------------------------------
# Conversão dos valores digitados
# ---------------------------------------------------------------------------
def _inteiro(valor: str, nome: str) -> int:
    s = valor.strip()
    try:
        return int(s, 10)
    except ValueError:
        pass
    try:
        return int(s, 0)  # aceita 0xACE1, 0b1010...
    except ValueError:
        raise ValueError(f"'{nome}' deve ser um número inteiro.")


def _matriz(valor: str) -> list:
    linhas = [l for l in valor.strip().splitlines() if l.strip()]
    if not linhas:
        raise ValueError("Informe a matriz-chave.")
    matriz = []
    for l in linhas:
        try:
            matriz.append([int(x) for x in l.replace(",", " ").split()])
        except ValueError:
            raise ValueError("A matriz deve conter apenas números inteiros.")
    if len(matriz) > LIMITE_MATRIZ:
        raise ValueError(f"A matriz pode ter no máximo {LIMITE_MATRIZ} linhas.")
    return matriz


def _taps(valor: str) -> tuple:
    partes = valor.replace(",", " ").split()
    if not partes:
        raise ValueError("Informe ao menos um tap (ex.: 0,2,3,5).")
    return tuple(_inteiro(p, "taps") for p in partes)


def _hex_para_bytes(valor: str) -> bytes:
    limpo = "".join(valor.split())
    try:
        return bytes.fromhex(limpo)
    except ValueError:
        raise ValueError(
            "O texto cifrado deve estar em hexadecimal (ex.: bbf316e8d940)."
        )


def _bytes_para_texto(dados: bytes) -> str:
    return dados.decode("utf-8", errors="replace")


def _formatar_matriz(matriz: list) -> str:
    largura = max(len(str(x)) for linha in matriz for x in linha)
    return "\n".join(" ".join(str(x).rjust(largura) for x in linha)
                     for linha in matriz)


# ---------------------------------------------------------------------------
# Execução: (cifra, operação) -> função(valores) -> texto do resultado
# ---------------------------------------------------------------------------
def _lfsr_params(v):
    return dict(
        semente=_inteiro(v["semente"], "semente"),
        taps=_taps(v["taps"]),
        tamanho=_inteiro(v["tamanho"], "tamanho"),
    )


def _lfsr_limitar(p):
    if p["tamanho"] > LIMITE_TAMANHO_LFSR:
        raise ValueError(
            f"O registrador pode ter no máximo {LIMITE_TAMANHO_LFSR} bits."
        )
    return p


def _gerar_fluxo(v):
    n = _inteiro(v["n_bytes"], "quantidade de bytes")
    if n > LIMITE_BYTES_FLUXO:
        raise ValueError(f"Peça no máximo {LIMITE_BYTES_FLUXO} bytes.")
    p = _lfsr_limitar(_lfsr_params(v))
    return cifras.lfsr_gerar_bytes(p["semente"], n, p["taps"], p["tamanho"]).hex()


def _forca_bruta(v):
    tentativas = cifras.cesar_forca_bruta(v["texto"])
    return "\n".join(f"Chave {k:>2}: {t}" for k, t in tentativas.items())


EXECUTORES = {
    ("cesar", "cifrar"): lambda v: cifras.cesar_cifrar(
        v["texto"], _inteiro(v["chave"], "chave")),
    ("cesar", "decifrar"): lambda v: cifras.cesar_decifrar(
        v["texto"], _inteiro(v["chave"], "chave")),
    ("cesar", "forca_bruta"): _forca_bruta,

    ("substituicao", "cifrar"): lambda v: cifras.substituicao_cifrar(
        v["texto"], v["chave"].strip()),
    ("substituicao", "decifrar"): lambda v: cifras.substituicao_decifrar(
        v["texto"], v["chave"].strip()),
    ("substituicao", "gerar_chave"): lambda v: cifras.gerar_chave_substituicao(),

    ("afim", "cifrar"): lambda v: cifras.afim_cifrar(
        v["texto"], _inteiro(v["a"], "a"), _inteiro(v["b"], "b")),
    ("afim", "decifrar"): lambda v: cifras.afim_decifrar(
        v["texto"], _inteiro(v["a"], "a"), _inteiro(v["b"], "b")),

    ("vigenere", "cifrar"): lambda v: cifras.vigenere_cifrar(
        v["texto"], v["chave"]),
    ("vigenere", "decifrar"): lambda v: cifras.vigenere_decifrar(
        v["texto"], v["chave"]),

    ("hill", "cifrar"): lambda v: cifras.hill_cifrar(
        v["texto"], _matriz(v["matriz"])),
    ("hill", "decifrar"): lambda v: cifras.hill_decifrar(
        v["texto"], _matriz(v["matriz"])),
    ("hill", "matriz_inversa"): lambda v: _formatar_matriz(
        cifras.hill_matriz_inversa(_matriz(v["matriz"]))),

    ("transposicao", "cifrar"): lambda v: cifras.transposicao_cifrar(
        v["texto"], v["chave"]),
    ("transposicao", "decifrar"): lambda v: cifras.transposicao_decifrar(
        v["texto"], v["chave"]),

    ("lfsr", "cifrar"): lambda v: cifras.fluxo_lfsr(
        v["texto"].encode("utf-8"),
        **_lfsr_limitar(_lfsr_params(v))).hex(),
    ("lfsr", "decifrar"): lambda v: _bytes_para_texto(cifras.fluxo_lfsr(
        _hex_para_bytes(v["texto"]),
        **_lfsr_limitar(_lfsr_params(v)))),
    ("lfsr", "gerar_fluxo"): _gerar_fluxo,

    ("rc4", "cifrar"): lambda v: cifras.rc4(
        v["texto"].encode("utf-8"), v["chave"].encode("utf-8")).hex(),
    ("rc4", "decifrar"): lambda v: _bytes_para_texto(cifras.rc4(
        _hex_para_bytes(v["texto"]), v["chave"].encode("utf-8"))),
}


def _limpar_mensagem(e: Exception) -> str:
    msg = str(e)
    return msg[len("ERRO: "):] if msg.startswith("ERRO: ") else msg


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------
@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/cifras")
def api_cifras():
    return jsonify(CIFRAS)


@app.post("/api/executar")
def api_executar():
    dados = request.get_json(silent=True) or {}
    cifra_id = dados.get("cifra")
    operacao = dados.get("operacao")
    valores = dados.get("valores") or {}

    cifra = CIFRAS_POR_ID.get(cifra_id)
    executor = EXECUTORES.get((cifra_id, operacao))
    if cifra is None or executor is None:
        return jsonify(ok=False, erro="Cifra ou operação desconhecida."), 400

    # Confere os campos que a operação escolhida exige
    v = {}
    for campo in cifra["campos"]:
        if campo["ops"] is not None and operacao not in campo["ops"]:
            continue
        bruto = valores.get(campo["id"], "")
        if not isinstance(bruto, str):
            bruto = str(bruto)
        if len(bruto) > LIMITE_TEXTO:
            return jsonify(ok=False, erro=f"'{campo['rotulo']}' é grande "
                           f"demais (máximo {LIMITE_TEXTO} caracteres)."), 400
        if bruto.strip() == "":
            rotulo = campo["rotulos"].get(operacao, campo["rotulo"])
            return jsonify(ok=False,
                           erro=f"Preencha o campo \"{rotulo}\"."), 400
        v[campo["id"]] = bruto

    try:
        resultado = executor(v)
    except (ValueError, TypeError) as e:
        return jsonify(ok=False, erro=_limpar_mensagem(e)), 400

    return jsonify(ok=True, resultado=resultado)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
