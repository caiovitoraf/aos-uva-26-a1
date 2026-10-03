"""Leitura dos documentos e integração entre vocabulário, Trie e Hash."""

from dataclasses import dataclass
from pathlib import Path
from time import perf_counter

from metricas import ContadorPassos, ordenar_com_passos
from preprocessamento import preprocessar
from trie import Trie


@dataclass(frozen=True)
class Documento:
    nome: str
    tokens: int
    tokens_sem_stopwords: int


def descobrir_documentos(pasta: Path) -> tuple[list[Path], list[str]]:
    try:
        arquivos = sorted(
            (p for p in pasta.iterdir() if p.is_file() and p.suffix.lower() == ".txt"),
            key=lambda p: p.name,
        )
    except OSError as erro:
        return [], [f"Não foi possível acessar a pasta de documentos: {erro}"]
    return arquivos, []


class MecanismoBusca:
    def __init__(self) -> None:
        self.trie = Trie()
        self.indice: dict[str, set[str]] = {}
        self.documentos: list[Documento] = []
        self.avisos: list[str] = []
        self.tempo_preprocessamento = 0.0
        self.tempo_indice = 0.0
        self.tempo_trie = 0.0

    @classmethod
    def construir(cls, arquivos: list[Path], stopwords: set[str]) -> "MecanismoBusca":
        mecanismo = cls()
        for arquivo in arquivos:
            try:
                texto = arquivo.read_text(encoding="utf-8-sig")
            except (OSError, UnicodeError) as erro:
                mecanismo.avisos.append(f"Arquivo ignorado ({arquivo.name}): {erro}")
                continue
            inicio = perf_counter()
            tokens, filtrados = preprocessar(texto, stopwords)
            mecanismo.tempo_preprocessamento += perf_counter() - inicio
            mecanismo.documentos.append(Documento(arquivo.name, len(tokens), len(filtrados)))

            inicio = perf_counter()
            # Set elimina repetições no mesmo documento; dict localiza o termo.
            for termo in set(filtrados):
                mecanismo.indice.setdefault(termo, set()).add(arquivo.name)
            mecanismo.tempo_indice += perf_counter() - inicio

        # As chaves distintas do índice constituem o vocabulário.
        inicio = perf_counter()
        for termo in mecanismo.indice:
            mecanismo.trie.inserir(termo)
        mecanismo.tempo_trie = perf_counter() - inicio
        return mecanismo

    @classmethod
    def carregar_pasta(cls, pasta: Path, stopwords: set[str]) -> "MecanismoBusca":
        arquivos, avisos = descobrir_documentos(pasta)
        mecanismo = cls.construir(arquivos, stopwords)
        mecanismo.avisos = avisos + mecanismo.avisos
        return mecanismo

    def buscar_palavra(self, termo: str, contador: ContadorPassos | None = None) -> list[str]:
        if contador is not None:
            contador.contar("Consultas ao índice Hash")
        documentos = self.indice.get(termo, set())
        if contador is not None:
            contador.contar("Documentos recuperados", len(documentos))
        return ordenar_com_passos(documentos, contador)

    def buscar_prefixo(self, prefixo: str, contador: ContadorPassos | None = None) -> dict[str, list[str]]:
        # O mesmo contador acumula o percurso da Trie e a recuperação no índice.
        return {termo: self.buscar_palavra(termo, contador)
                for termo in self.trie.buscar_prefixo(prefixo, contador)}

    def estatisticas(self) -> dict[str, int | float]:
        return {
            "documentos": len(self.documentos),
            "tokens": sum(d.tokens for d in self.documentos),
            "tokens_sem_stopwords": sum(d.tokens_sem_stopwords for d in self.documentos),
            "termos_distintos": len(self.indice),
            "palavras_trie": self.trie.quantidade_palavras,
            "tempo_preprocessamento_s": self.tempo_preprocessamento,
            "tempo_indice_s": self.tempo_indice,
            "tempo_trie_s": self.tempo_trie,
        }
