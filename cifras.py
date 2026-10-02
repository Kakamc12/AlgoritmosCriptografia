# -*- coding: utf-8 -*-
"""
cifras
======

Biblioteca de cifras clássicas e de fluxo. Depende do módulo `criptomat`
(deve estar na mesma pasta), do qual reutiliza aritmética modular, MDC e
inverso multiplicativo.

Cifras disponíveis:
    1. César ................ cesar_cifrar, cesar_decifrar, cesar_forca_bruta
    2. Substituição ......... gerar_chave_substituicao,
                              substituicao_cifrar, substituicao_decifrar
    3. Afim ................. afim_cifrar, afim_decifrar
    4. Vigenère ............. vigenere_cifrar, vigenere_decifrar
    5. Hill ................. hill_cifrar, hill_decifrar, hill_matriz_inversa
    6. Transposição ......... transposicao_cifrar, transposicao_decifrar
    7. Cifras de fluxo ...... lfsr_gerar_bytes, fluxo_lfsr, rc4

Convenções:
    - Cifras clássicas (César, substituição, Afim, Vigenère) trabalham com o
      alfabeto A-Z (26 letras). Mantêm maiúsculas/minúsculas e deixam
      inalterados espaços, números, pontuação e letras acentuadas.
    - Hill remove tudo que não for letra e devolve texto em maiúsculas.
    - Cifras de fluxo trabalham com `bytes`.
"""

import secrets

from criptomat import (
    Mod_Add,
    Mod_Sub,
    Mod_Mul,
    Sao_Coprimos,
    inverso_multiplicativo,
)

__all__ = [
    "cesar_cifrar", "cesar_decifrar", "cesar_forca_bruta",
    "gerar_chave_substituicao", "substituicao_cifrar", "substituicao_decifrar",
    "afim_cifrar", "afim_decifrar",
    "vigenere_cifrar", "vigenere_decifrar",
    "hill_cifrar", "hill_decifrar", "hill_matriz_inversa",
    "transposicao_cifrar", "transposicao_decifrar",
    "lfsr_gerar_bytes", "fluxo_lfsr", "rc4",
]

__version__ = "1.0.0"

ALFABETO = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
N = len(ALFABETO)  # 26


# ---------------------------------------------------------------------------
# Auxiliares internos
# ---------------------------------------------------------------------------
def _eh_letra(c: str) -> bool:
    """True apenas para letras ASCII A-Z / a-z."""
    return ("A" <= c <= "Z") or ("a" <= c <= "z")


def _base(c: str) -> int:
    return ord("A") if c.isupper() else ord("a")


def _mapear_letras(texto: str, funcao) -> str:
    """
    Aplica `funcao(posicao_da_letra_0_a_25)` em cada letra do texto,
    preservando caixa e mantendo os demais caracteres.
    """
    resultado = []
    for c in texto:
        if _eh_letra(c):
            base = _base(c)
            resultado.append(chr(funcao(ord(c) - base) + base))
        else:
            resultado.append(c)
    return "".join(resultado)


def _checar_texto(texto) -> None:
    if not isinstance(texto, str):
        raise TypeError("ERRO: O texto deve ser uma string.")


def _checar_int(valor, nome: str) -> None:
    if not isinstance(valor, int) or isinstance(valor, bool):
        raise TypeError(f"ERRO: '{nome}' deve ser um inteiro.")


def _somente_letras(texto: str) -> str:
    """Remove tudo que não for letra ASCII e converte para maiúsculas."""
    return "".join(c.upper() for c in texto if _eh_letra(c))


def _chave_para_deslocamentos(chave: str) -> list:
    letras = _somente_letras(chave)
    if not letras:
        raise ValueError("ERRO: A chave deve conter ao menos uma letra (A-Z).")
    return [ord(c) - ord("A") for c in letras]


# ---------------------------------------------------------------------------
# 1- Cifra de César
# ---------------------------------------------------------------------------
def cesar_cifrar(texto: str, chave: int) -> str:
    """C = (P + chave) mod 26."""
    _checar_texto(texto)
    _checar_int(chave, "chave")
    return _mapear_letras(texto, lambda p: Mod_Add(p, chave, N))


def cesar_decifrar(texto: str, chave: int) -> str:
    """P = (C - chave) mod 26."""
    _checar_texto(texto)
    _checar_int(chave, "chave")
    return _mapear_letras(texto, lambda c: Mod_Sub(c, chave, N))


def cesar_forca_bruta(texto: str) -> dict:
    """Ataque por força bruta: retorna {chave: texto_decifrado} para 0..25."""
    _checar_texto(texto)
    return {k: cesar_decifrar(texto, k) for k in range(N)}


# ---------------------------------------------------------------------------
# 2- Cifra de substituição (monoalfabética)
# ---------------------------------------------------------------------------
def _validar_chave_substituicao(chave: str) -> str:
    _checar_texto(chave)
    chave = chave.upper()
    if len(chave) != N or set(chave) != set(ALFABETO):
        raise ValueError(
            "ERRO: A chave deve ser uma permutação das 26 letras do alfabeto, "
            "sem repetições."
        )
    return chave


def gerar_chave_substituicao() -> str:
    """Gera uma chave aleatória (permutação de A-Z) usando `secrets`."""
    letras = list(ALFABETO)
    secrets.SystemRandom().shuffle(letras)
    return "".join(letras)


def substituicao_cifrar(texto: str, chave: str) -> str:
    """
    Substitui cada letra do alfabeto pela letra na mesma posição da chave.
    Ex.: chave = "QWERTYUIOPASDFGHJKLZXCVBNM" troca A->Q, B->W, C->E, ...
    """
    _checar_texto(texto)
    chave = _validar_chave_substituicao(chave)
    return _mapear_letras(texto, lambda p: ord(chave[p]) - ord("A"))


def substituicao_decifrar(texto: str, chave: str) -> str:
    """Operação inversa de `substituicao_cifrar`."""
    _checar_texto(texto)
    chave = _validar_chave_substituicao(chave)
    inversa = {ord(letra) - ord("A"): i for i, letra in enumerate(chave)}
    return _mapear_letras(texto, lambda c: inversa[c])


# ---------------------------------------------------------------------------
# 3- Cifra Afim
# ---------------------------------------------------------------------------
def _validar_afim(a: int, b: int) -> None:
    _checar_int(a, "a")
    _checar_int(b, "b")
    if not Sao_Coprimos(a % N, N):
        raise ValueError(
            f"ERRO: 'a' = {a} não é coprimo com {N}; a cifra não seria "
            f"reversível."
        )


def afim_cifrar(texto: str, a: int, b: int) -> str:
    """C = (a*P + b) mod 26, com MDC(a, 26) = 1."""
    _checar_texto(texto)
    _validar_afim(a, b)
    return _mapear_letras(texto, lambda p: Mod_Add(Mod_Mul(a, p, N), b, N))


def afim_decifrar(texto: str, a: int, b: int) -> str:
    """P = a^-1 * (C - b) mod 26."""
    _checar_texto(texto)
    _validar_afim(a, b)
    a_inv = inverso_multiplicativo(a % N, N)
    return _mapear_letras(texto, lambda c: Mod_Mul(a_inv, Mod_Sub(c, b, N), N))


# ---------------------------------------------------------------------------
# 4- Cifra de Vigenère
# ---------------------------------------------------------------------------
def vigenere_cifrar(texto: str, chave: str) -> str:
    """Soma, letra a letra, os deslocamentos da chave (repetida) mod 26."""
    _checar_texto(texto)
    _checar_texto(chave)
    desloc = _chave_para_deslocamentos(chave)

    resultado = []
    i = 0  # a chave só avança em letras
    for c in texto:
        if _eh_letra(c):
            base = _base(c)
            k = desloc[i % len(desloc)]
            resultado.append(chr(Mod_Add(ord(c) - base, k, N) + base))
            i += 1
        else:
            resultado.append(c)
    return "".join(resultado)


def vigenere_decifrar(texto: str, chave: str) -> str:
    """Operação inversa de `vigenere_cifrar`."""
    _checar_texto(texto)
    _checar_texto(chave)
    desloc = _chave_para_deslocamentos(chave)

    resultado = []
    i = 0
    for c in texto:
        if _eh_letra(c):
            base = _base(c)
            k = desloc[i % len(desloc)]
            resultado.append(chr(Mod_Sub(ord(c) - base, k, N) + base))
            i += 1
        else:
            resultado.append(c)
    return "".join(resultado)


# ---------------------------------------------------------------------------
# 5- Cifra de Hill
# ---------------------------------------------------------------------------
def _validar_matriz(matriz: list) -> int:
    if not isinstance(matriz, list) or len(matriz) == 0:
        raise ValueError("ERRO: A chave deve ser uma matriz (lista de listas).")
    n = len(matriz)
    for linha in matriz:
        if not isinstance(linha, list) or len(linha) != n:
            raise ValueError("ERRO: A matriz-chave deve ser quadrada.")
        for x in linha:
            _checar_int(x, "elemento da matriz")
    return n


def _menor(matriz: list, i: int, j: int) -> list:
    """Submatriz sem a linha i e a coluna j."""
    return [
        [x for c, x in enumerate(linha) if c != j]
        for r, linha in enumerate(matriz) if r != i
    ]


def _determinante(matriz: list) -> int:
    """Determinante por expansão de Laplace (adequado a matrizes pequenas)."""
    n = len(matriz)
    if n == 1:
        return matriz[0][0]
    if n == 2:
        return matriz[0][0] * matriz[1][1] - matriz[0][1] * matriz[1][0]
    return sum(
        ((-1) ** j) * matriz[0][j] * _determinante(_menor(matriz, 0, j))
        for j in range(n)
    )


def hill_matriz_inversa(matriz: list) -> list:
    """
    Retorna a inversa da matriz-chave módulo 26:
        K^-1 = det(K)^-1 * adj(K)  (mod 26)
    Lança ValueError se MDC(det, 26) != 1.
    """
    n = _validar_matriz(matriz)
    det = _determinante(matriz) % N

    if not Sao_Coprimos(det, N):
        raise ValueError(
            f"ERRO: A matriz não é invertível módulo {N} "
            f"(det = {det}, MDC(det, {N}) != 1)."
        )

    det_inv = inverso_multiplicativo(det, N)

    if n == 1:
        return [[det_inv % N]]

    # adjunta = transposta da matriz de cofatores
    inversa = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            cofator = ((-1) ** (i + j)) * _determinante(_menor(matriz, i, j))
            inversa[j][i] = Mod_Mul(det_inv, cofator, N)
    return inversa


def _hill_aplicar(texto: str, matriz: list, preencher: bool) -> str:
    n = _validar_matriz(matriz)
    letras = _somente_letras(texto)

    if preencher and len(letras) % n != 0:
        letras += "X" * (n - len(letras) % n)
    if len(letras) % n != 0:
        raise ValueError(
            f"ERRO: O tamanho do texto cifrado deve ser múltiplo de {n}."
        )

    resultado = []
    for inicio in range(0, len(letras), n):
        bloco = [ord(c) - ord("A") for c in letras[inicio:inicio + n]]
        for i in range(n):
            soma = 0
            for j in range(n):
                soma = Mod_Add(soma, Mod_Mul(matriz[i][j], bloco[j], N), N)
            resultado.append(ALFABETO[soma])
    return "".join(resultado)


def hill_cifrar(texto: str, matriz: list) -> str:
    """
    Cifra em blocos de tamanho n (n = ordem da matriz): C = K * P (mod 26).
    Só letras são consideradas; se faltar, completa com 'X'.
    Retorna texto em maiúsculas.
    """
    _checar_texto(texto)
    hill_matriz_inversa(matriz)  # garante que a chave é válida
    return _hill_aplicar(texto, matriz, preencher=True)


def hill_decifrar(texto: str, matriz: list) -> str:
    """
    P = K^-1 * C (mod 26). Retorna texto em maiúsculas
    (eventuais 'X' de preenchimento no final permanecem).
    """
    _checar_texto(texto)
    inversa = hill_matriz_inversa(matriz)
    return _hill_aplicar(texto, inversa, preencher=False)


# ---------------------------------------------------------------------------
# 6- Cifra de transposição (colunar, com palavra-chave)
# ---------------------------------------------------------------------------
def _ordem_colunas(chave: str) -> list:
    """Ordem de leitura das colunas: pela ordem alfabética das letras da chave."""
    _checar_texto(chave)
    if len(chave) == 0:
        raise ValueError("ERRO: A chave não pode ser vazia.")
    return sorted(range(len(chave)), key=lambda i: (chave[i], i))


def transposicao_cifrar(texto: str, chave: str) -> str:
    """
    Escreve o texto em linhas, com tantas colunas quanto o tamanho da chave,
    e lê as colunas na ordem alfabética das letras da chave.
    Todos os caracteres (inclusive espaços) são preservados.
    """
    _checar_texto(texto)
    ordem = _ordem_colunas(chave)
    k = len(chave)
    return "".join(texto[col::k] for col in ordem)


def transposicao_decifrar(texto: str, chave: str) -> str:
    """Operação inversa de `transposicao_cifrar`."""
    _checar_texto(texto)
    ordem = _ordem_colunas(chave)
    k = len(chave)
    tamanho = len(texto)

    # colunas mais à esquerda podem ter uma linha a mais
    colunas = {}
    pos = 0
    for col in ordem:
        comprimento = tamanho // k + (1 if col < tamanho % k else 0)
        colunas[col] = texto[pos:pos + comprimento]
        pos += comprimento

    return "".join(colunas[i % k][i // k] for i in range(tamanho))


# ---------------------------------------------------------------------------
# 7- Cifras de fluxo
# ---------------------------------------------------------------------------
def _xor_bytes(dados: bytes, fluxo: bytes) -> bytes:
    return bytes(d ^ f for d, f in zip(dados, fluxo))


def lfsr_gerar_bytes(semente: int, n_bytes: int,
                     taps: tuple = (0, 2, 3, 5), tamanho: int = 16) -> bytes:
    """
    Gera `n_bytes` de fluxo de chave com um LFSR (registrador de deslocamento
    com realimentação linear).

    semente : estado inicial (inteiro entre 1 e 2**tamanho - 1)
    taps    : posições dos bits (0 = menos significativo) usadas na
              realimentação. O padrão (0, 2, 3, 5) com tamanho 16 corresponde
              ao polinômio x^16 + x^14 + x^13 + x^11 + 1 (período máximo).
    tamanho : número de bits do registrador.
    """
    _checar_int(semente, "semente")
    _checar_int(n_bytes, "n_bytes")
    _checar_int(tamanho, "tamanho")

    if tamanho <= 0:
        raise ValueError("ERRO: O tamanho do registrador deve ser positivo.")
    if not 0 < semente < (1 << tamanho):
        raise ValueError(
            f"ERRO: A semente deve estar entre 1 e {(1 << tamanho) - 1}."
        )
    if n_bytes < 0:
        raise ValueError("ERRO: n_bytes não pode ser negativo.")
    if len(taps) == 0 or any(t < 0 or t >= tamanho for t in taps):
        raise ValueError("ERRO: Os taps devem estar entre 0 e tamanho - 1.")

    estado = semente
    saida = bytearray()
    for _ in range(n_bytes):
        byte = 0
        for _ in range(8):
            bit_saida = estado & 1
            realimentacao = 0
            for t in taps:
                realimentacao ^= (estado >> t) & 1
            estado = (estado >> 1) | (realimentacao << (tamanho - 1))
            byte = (byte << 1) | bit_saida
        saida.append(byte)
    return bytes(saida)


def fluxo_lfsr(dados: bytes, semente: int,
               taps: tuple = (0, 2, 3, 5), tamanho: int = 16) -> bytes:
    """
    Cifra/decifra `dados` fazendo XOR com o fluxo gerado pelo LFSR.
    A mesma função cifra e decifra (com a mesma semente).

    Atenção: LFSR isolado é linear e NÃO é seguro; serve para fins didáticos.
    """
    if not isinstance(dados, (bytes, bytearray)):
        raise TypeError("ERRO: 'dados' deve ser do tipo bytes.")
    fluxo = lfsr_gerar_bytes(semente, len(dados), taps, tamanho)
    return _xor_bytes(dados, fluxo)


def rc4(dados: bytes, chave: bytes) -> bytes:
    """
    Cifra/decifra `dados` com RC4. A mesma função cifra e decifra.

    Atenção: RC4 é considerado inseguro atualmente; use apenas para estudo.
    """
    if not isinstance(dados, (bytes, bytearray)):
        raise TypeError("ERRO: 'dados' deve ser do tipo bytes.")
    if not isinstance(chave, (bytes, bytearray)):
        raise TypeError("ERRO: 'chave' deve ser do tipo bytes.")
    if not 1 <= len(chave) <= 256:
        raise ValueError("ERRO: A chave RC4 deve ter entre 1 e 256 bytes.")

    # KSA: inicialização da permutação
    S = list(range(256))
    j = 0
    for i in range(256):
        j = Mod_Add(Mod_Add(j, S[i], 256), chave[i % len(chave)], 256)
        S[i], S[j] = S[j], S[i]

    # PRGA: geração do fluxo e XOR
    saida = bytearray()
    i = j = 0
    for byte in dados:
        i = Mod_Add(i, 1, 256)
        j = Mod_Add(j, S[i], 256)
        S[i], S[j] = S[j], S[i]
        k = S[Mod_Add(S[i], S[j], 256)]
        saida.append(byte ^ k)
    return bytes(saida)
