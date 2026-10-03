"""Normalização Unicode, tokenização e remoção de stopwords."""

from pathlib import Path
import unicodedata


def tokenizar(texto: str) -> list[str]:
    """Preserva letras, números e marcas Unicode; separa pontuação e símbolos."""
    texto = unicodedata.normalize("NFC", texto)
    texto = unicodedata.normalize("NFC", texto.lower())
    caracteres = [
        c if unicodedata.category(c)[0] in {"L", "N", "M"} else " "
        for c in texto
    ]
    return "".join(caracteres).split()


def carregar_stopwords(caminho: Path) -> set[str]:
    """Uma palavra por linha; linhas iniciadas por # são comentários."""
    palavras: set[str] = set()
    for numero, linha in enumerate(caminho.read_text(encoding="utf-8-sig").splitlines(), 1):
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        tokens = tokenizar(linha)
        if len(tokens) != 1:
            raise ValueError(f"Stopword inválida na linha {numero}: use uma palavra.")
        palavras.add(tokens[0])
    return palavras


def preprocessar(texto: str, stopwords: set[str]) -> tuple[list[str], list[str]]:
    tokens = tokenizar(texto)
    return tokens, [token for token in tokens if token not in stopwords]


def normalizar_termo(texto: str, stopwords: set[str] | None = None) -> str:
    tokens = tokenizar(texto)
    if len(tokens) != 1:
        raise ValueError("Informe uma única palavra ou prefixo não vazio.")
    termo = tokens[0]
    if stopwords is not None and termo in stopwords:
        raise ValueError(f"'{termo}' é uma stopword e não está no índice.")
    return termo
