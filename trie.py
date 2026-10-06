from dataclasses import dataclass, field

from metricas import ContadorPassos, ordenar_com_passos


@dataclass
class NoTrie:
    filhos: dict[str, "NoTrie"] = field(default_factory=dict)
    fim_palavra: bool = False


class Trie:
    def __init__(self) -> None:
        self.raiz = NoTrie()
        self.quantidade_palavras = 0

    def inserir(self, palavra: str, contador: ContadorPassos | None = None) -> bool:
        """Retorna True somente se uma palavra nova foi inserida."""
        if not palavra:
            raise ValueError("A palavra não pode ser vazia.")
        no = self.raiz
        for caractere in palavra:
            if contador is not None:
                contador.contar("Caracteres da palavra examinados")
            if caractere not in no.filhos:
                no.filhos[caractere] = NoTrie()
                if contador is not None:
                    contador.contar("Nós criados")
            no = no.filhos[caractere]
        if contador is not None:
            contador.contar("Finais de palavra verificados")
        if no.fim_palavra:
            return False
        no.fim_palavra = True
        self.quantidade_palavras += 1
        if contador is not None:
            contador.contar("Palavras cadastradas")
        return True

    def _percorrer(self, texto: str, contador: ContadorPassos | None = None) -> NoTrie | None:
        no = self.raiz
        for caractere in texto:
            if contador is not None:
                contador.contar("Caracteres do caminho examinados")
            no = no.filhos.get(caractere)
            if no is None:
                return None
        return no

    def buscar(self, palavra: str, contador: ContadorPassos | None = None) -> bool:
        no = self._percorrer(palavra, contador)
        if palavra and no is not None and contador is not None:
            contador.contar("Finais de palavra verificados")
        return bool(palavra and no is not None and no.fim_palavra)

    def buscar_prefixo(self, prefixo: str, contador: ContadorPassos | None = None) -> list[str]:
        if not prefixo:
            raise ValueError("O prefixo não pode ser vazio.")
        no = self._percorrer(prefixo, contador)
        if no is None:
            return []
        if contador is not None:
            contador.contar("Finais de palavra verificados")
        palavras = [prefixo] if no.fim_palavra else []
        if palavras and contador is not None:
            contador.contar("Palavras recuperadas")
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
            if contador is not None:
                contador.contar("Nós descendentes visitados")
                contador.contar("Finais de palavra verificados")
            caminho.append(caractere)
            if filho.fim_palavra:
                palavras.append("".join(caminho))
                if contador is not None:
                    contador.contar("Palavras recuperadas")
                    contador.contar("Caracteres copiados para sugestões", len(caminho))
            pilha.append(iter(filho.filhos.items()))
        return ordenar_com_passos(palavras, contador)
