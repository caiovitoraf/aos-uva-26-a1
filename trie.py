"""Trie implementada sem bibliotecas externas, compartilhada pelas duas partes."""

from dataclasses import dataclass, field


@dataclass
class NoTrie:
    filhos: dict[str, "NoTrie"] = field(default_factory=dict)
    fim_palavra: bool = False


class Trie:
    def __init__(self) -> None:
        self.raiz = NoTrie()
        self.quantidade_palavras = 0

    def inserir(self, palavra: str) -> bool:
        """Retorna True somente se uma palavra nova foi inserida."""
        if not palavra:
            raise ValueError("A palavra não pode ser vazia.")
        no = self.raiz
        for caractere in palavra:
            if caractere not in no.filhos:
                no.filhos[caractere] = NoTrie()
            no = no.filhos[caractere]
        if no.fim_palavra:
            return False
        no.fim_palavra = True
        self.quantidade_palavras += 1
        return True

    def _percorrer(self, texto: str) -> NoTrie | None:
        no = self.raiz
        for caractere in texto:
            no = no.filhos.get(caractere)
            if no is None:
                return None
        return no

    def buscar(self, palavra: str) -> bool:
        no = self._percorrer(palavra)
        return bool(palavra and no is not None and no.fim_palavra)

    def buscar_prefixo(self, prefixo: str) -> list[str]:
        if not prefixo:
            raise ValueError("O prefixo não pode ser vazio.")
        no = self._percorrer(prefixo)
        if no is None:
            return []
        palavras = [prefixo] if no.fim_palavra else []
        caminho = list(prefixo)
        # DFS iterativa: cada aresta é visitada uma vez. Evita limite de recursão
        # e evita copiar a string inteira em cada nó intermediário.
        pilha = [iter(no.filhos.items())]
        while pilha:
            proximo = next(pilha[-1], None)
            if proximo is None:
                pilha.pop()
                if pilha:
                    caminho.pop()
                continue
            caractere, filho = proximo
            caminho.append(caractere)
            if filho.fim_palavra:
                palavras.append("".join(caminho))
            pilha.append(iter(filho.filhos.items()))
        return sorted(palavras)
