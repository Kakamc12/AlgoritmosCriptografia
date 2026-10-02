# -*- coding: utf-8 -*-
"""
criptomat
=========

Biblioteca de algoritmos de teoria dos números usados em criptografia.

Funções disponíveis:
    1. Aritmética modular ......... Mod_Add, Mod_Sub, Mod_Mul
    2. Máximo divisor comum ....... MDC, Sao_Coprimos
    3. Algoritmo de Euclides ...... algoritmo_euclides
    4. Euclides estendido ......... euclides_estendido
    5. Inverso multiplicativo ..... inverso_multiplicativo
    6. Números primos ............. Eh_Primo, Gerar_Primo
    7. Função φ de Euler .......... funcao_euler
    8. Exponenciação modular ...... exponenciacao_modular
    9. Teorema Chinês do Resto .... TeoremaChinesResto

Exemplo de uso:
    >>> import criptomat
    >>> criptomat.MDC(48, 18)
    6
"""

import secrets

__all__ = [
    "Mod_Add", "Mod_Sub", "Mod_Mul",
    "MDC", "Sao_Coprimos",
    "algoritmo_euclides",
    "euclides_estendido",
    "inverso_multiplicativo",
    "Eh_Primo", "Gerar_Primo",
    "funcao_euler",
    "exponenciacao_modular",
    "TeoremaChinesResto",
]

__version__ = "1.0.0"


# ---------------------------------------------------------------------------
# Funções auxiliares internas (não fazem parte da API pública)
# ---------------------------------------------------------------------------
def _checar_inteiros(**valores) -> None:
    for nome, valor in valores.items():
        # bool é subclasse de int; rejeitamos para evitar True/False como número
        if not isinstance(valor, int) or isinstance(valor, bool):
            raise TypeError(f"ERRO: '{nome}' deve ser um inteiro.")


def _checar_modulo(n: int) -> None:
    _checar_inteiros(n=n)
    if n <= 0:
        raise ValueError("ERRO: O módulo n deve ser maior que zero.")


# ---------------------------------------------------------------------------
# 1- Aritmética modular
# ---------------------------------------------------------------------------
def Mod_Add(a: int, b: int, n: int) -> int:
    """Soma modular: retorna (a + b) mod n."""
    _checar_inteiros(a=a, b=b)
    _checar_modulo(n)
    return ((a % n) + (b % n)) % n


def Mod_Sub(a: int, b: int, n: int) -> int:
    """Subtração modular: retorna (a - b) mod n."""
    _checar_inteiros(a=a, b=b)
    _checar_modulo(n)
    return ((a % n) - (b % n)) % n


def Mod_Mul(a: int, b: int, n: int) -> int:
    """Multiplicação modular: retorna (a * b) mod n."""
    _checar_inteiros(a=a, b=b)
    _checar_modulo(n)
    return ((a % n) * (b % n)) % n


# ---------------------------------------------------------------------------
# 2- Máximo divisor comum
# ---------------------------------------------------------------------------
def MDC(a: int, b: int) -> int:
    """Retorna o máximo divisor comum de a e b (sempre não negativo)."""
    _checar_inteiros(a=a, b=b)

    a, b = abs(a), abs(b)

    if a == 0 and b == 0:
        raise ValueError("ERRO: MDC(0, 0) não está definido.")

    while b != 0:
        a, b = b, a % b

    return a


def Sao_Coprimos(a: int, b: int) -> bool:
    """Retorna True se MDC(a, b) == 1."""
    return MDC(a, b) == 1


# ---------------------------------------------------------------------------
# 3- Algoritmo de Euclides
# ---------------------------------------------------------------------------
def algoritmo_euclides(a: int, b: int) -> int:
    """Calcula o MDC pelo algoritmo de Euclides (divisões sucessivas)."""
    _checar_inteiros(a=a, b=b)

    a, b = abs(a), abs(b)

    if a == 0 and b == 0:
        raise ValueError("ERRO: MDC(0, 0) não está definido.")

    while b != 0:
        a, b = b, a % b

    return a


# ---------------------------------------------------------------------------
# 4- Algoritmo estendido de Euclides
# ---------------------------------------------------------------------------
def euclides_estendido(a: int, b: int) -> tuple:
    """
    Retorna a tupla (mdc, x, y) tal que a*x + b*y = mdc.
    """
    _checar_inteiros(a=a, b=b)

    r_ant, r_atu = a, b
    x_ant, x_atu = 1, 0
    y_ant, y_atu = 0, 1

    while r_atu != 0:
        q = r_ant // r_atu

        r_ant, r_atu = r_atu, r_ant - q * r_atu
        x_ant, x_atu = x_atu, x_ant - q * x_atu
        y_ant, y_atu = y_atu, y_ant - q * y_atu

    return r_ant, x_ant, y_ant


# ---------------------------------------------------------------------------
# 5- Inverso multiplicativo
# ---------------------------------------------------------------------------
def inverso_multiplicativo(a: int, m: int) -> int:
    """
    Retorna x tal que (a * x) mod m == 1.
    Lança ValueError se o inverso não existir (MDC(a, m) != 1).
    """
    _checar_inteiros(a=a, m=m)

    if m <= 0:
        raise ValueError("ERRO: O módulo deve ser maior que zero.")

    a = a % m
    divisor_comum, x, _ = euclides_estendido(a, m)

    if divisor_comum != 1:
        raise ValueError(
            f"ERRO: O inverso multiplicativo de {a} módulo {m} não existe, "
            f"pois MDC({a}, {m}) = {divisor_comum}."
        )

    return x % m


# ---------------------------------------------------------------------------
# 6- Números primos
# ---------------------------------------------------------------------------
def Eh_Primo(n: int) -> bool:
    """Testa se n é primo por divisão por tentativa (adequado a números pequenos)."""
    _checar_inteiros(n=n)

    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False

    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2

    return True


def Gerar_Primo(bits: int = 16) -> int:
    """
    Gera um primo aleatório com exatamente `bits` bits
    (usa o módulo `secrets`). Requer bits >= 2.
    Atenção: como usa Eh_Primo, é indicado para tamanhos pequenos (didático).
    """
    _checar_inteiros(bits=bits)
    if bits < 2:
        raise ValueError("ERRO: O número de bits deve ser pelo menos 2.")

    while True:
        candidato = secrets.randbits(bits)
        candidato |= (1 << (bits - 1)) | 1  # bit mais alto e bit menos significativo = 1
        if Eh_Primo(candidato):
            return candidato


# ---------------------------------------------------------------------------
# 7- Função φ de Euler
# ---------------------------------------------------------------------------
def funcao_euler(n: int) -> int:
    """Retorna φ(n): quantidade de inteiros em [1, n] coprimos com n."""
    _checar_inteiros(n=n)

    if n <= 0:
        raise ValueError("ERRO: O valor deve ser maior que zero.")

    contador = 0
    for i in range(1, n + 1):
        if Sao_Coprimos(i, n):
            contador += 1

    return contador


# ---------------------------------------------------------------------------
# 8- Exponenciação modular
# ---------------------------------------------------------------------------
def exponenciacao_modular(base: int, expoente: int, modulo: int) -> int:
    """Retorna (base ** expoente) mod modulo, por quadrados sucessivos."""
    _checar_inteiros(base=base, expoente=expoente, modulo=modulo)

    if modulo <= 0:
        raise ValueError("ERRO: O módulo deve ser maior que zero.")
    if expoente < 0:
        raise ValueError("ERRO: O expoente não pode ser negativo.")

    resultado = 1 % modulo
    base = base % modulo

    while expoente > 0:
        if expoente % 2 == 1:
            resultado = (resultado * base) % modulo
        base = (base * base) % modulo
        expoente //= 2

    return resultado


# ---------------------------------------------------------------------------
# 9- Teorema Chinês do Resto (módulos coprimos)
# ---------------------------------------------------------------------------
def TeoremaChinesResto(a: list, m: list) -> int:
    """
    Resolve o sistema  x ≡ a[i] (mod m[i])  com módulos dois a dois coprimos.
    Retorna a solução x em [0, M), onde M = produto dos módulos.
    """
    if len(a) != len(m):
        raise ValueError("ERRO TCR: a e m possuem tamanhos diferentes.")
    if len(m) == 0:
        raise ValueError("ERRO TCR: as listas não podem ser vazias.")

    for i in range(len(m)):
        for j in range(i + 1, len(m)):
            if not Sao_Coprimos(m[i], m[j]):
                raise ValueError(
                    f"ERRO TCR: os módulos {m[i]} e {m[j]} não são coprimos."
                )

    M = 1
    for modulo in m:
        M *= modulo

    soma = 0
    for ai, mi in zip(a, m):
        Mi = M // mi
        Mi_inv = inverso_multiplicativo(Mi % mi, mi)
        soma += ai * Mi * Mi_inv

    return soma % M
