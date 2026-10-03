"""Interface de terminal das duas partes do trabalho. Execute: python main.py."""

from pathlib import Path
from time import perf_counter

from indice_invertido import MecanismoBusca
from preprocessamento import carregar_stopwords, normalizar_termo
from trie import Trie

RAIZ = Path(__file__).resolve().parent


def ler_termo(mensagem: str, stopwords: set[str] | None = None) -> str | None:
    try:
        return normalizar_termo(input(mensagem), stopwords)
    except ValueError as erro:
        print(erro)
        return None


def carregar_autocomplete(caminho: Path) -> tuple[Trie, list[str]]:
    trie = Trie()
    avisos = []
    try:
        linhas = caminho.read_text(encoding="utf-8-sig").splitlines()
    except (OSError, UnicodeError) as erro:
        return trie, [f"Não foi possível carregar palavras iniciais: {erro}"]
    for numero, linha in enumerate(linhas, 1):
        if not linha.strip() or linha.strip().startswith("#"):
            continue
        try:
            trie.inserir(normalizar_termo(linha))
        except ValueError:
            avisos.append(f"Palavra inicial ignorada na linha {numero}: {linha}")
    return trie, avisos


def mostrar_tempo(inicio: float, fim: float) -> None:
    print(f"Tempo da consulta: {(fim - inicio) * 1000:.6f} ms")


def menu_autocomplete(trie: Trie) -> None:
    while True:
        print(f"\nAUTOCOMPLETE COM TRIE — {trie.quantidade_palavras} palavras")
        print("1 - Buscar palavra\n2 - Buscar por prefixo\n3 - Inserir palavra\n4 - Voltar")
        opcao = input("Escolha: ").strip()
        if opcao == "4":
            return
        if opcao not in {"1", "2", "3"}:
            print("Opção inválida.")
            continue
        termo = ler_termo("Digite a palavra ou prefixo: ")
        if termo is None:
            continue
        inicio = perf_counter()
        if opcao == "1":
            resultado = trie.buscar(termo)
        elif opcao == "2":
            resultado = trie.buscar_prefixo(termo)
        else:
            resultado = trie.inserir(termo)
        fim = perf_counter()
        if opcao == "1":
            print("Palavra encontrada." if resultado else "Palavra não encontrada.")
        elif opcao == "2":
            print("Palavras encontradas:" if resultado else "Nenhuma palavra encontrada.")
            for palavra in resultado:
                print(f"- {palavra}")
        else:
            print("Palavra inserida." if resultado else "A palavra já estava cadastrada.")
        if opcao in {"1", "2"}:
            mostrar_tempo(inicio, fim)


def mostrar_estatisticas(mecanismo: MecanismoBusca) -> None:
    e = mecanismo.estatisticas()
    print(f"Documentos processados: {e['documentos']}")
    print(f"Palavras após tokenização, antes das stopwords: {e['tokens']}")
    print(f"Palavras após remoção de stopwords: {e['tokens_sem_stopwords']}")
    print(f"Termos distintos: {e['termos_distintos']}")
    print(f"Palavras armazenadas na Trie: {e['palavras_trie']}")
    for chave, nome in [("tempo_preprocessamento_s", "Pré-processamento"),
                        ("tempo_trie_s", "Construção da Trie"),
                        ("tempo_indice_s", "Construção do índice invertido")]:
        print(f"{nome}: {e[chave] * 1000:.6f} ms")


def menu_documentos(mecanismo: MecanismoBusca, stopwords: set[str]) -> None:
    while True:
        print(f"\nBUSCA EM DOCUMENTOS — {len(mecanismo.documentos)} documentos")
        print("1 - Buscar palavra\n2 - Buscar por prefixo\n3 - Listar documentos\n4 - Estatísticas\n5 - Voltar")
        opcao = input("Escolha: ").strip()
        if opcao == "5":
            return
        if opcao == "3":
            for doc in mecanismo.documentos:
                print(f"- {doc.nome}: {doc.tokens} tokens; {doc.tokens_sem_stopwords} sem stopwords")
            if not mecanismo.documentos:
                print("Nenhum documento processado.")
        elif opcao == "4":
            mostrar_estatisticas(mecanismo)
        elif opcao in {"1", "2"}:
            # Prefixos podem coincidir com stopwords: 'de' ainda encontra 'desenvolvimento'.
            termo = ler_termo("Digite a palavra ou prefixo: ", stopwords if opcao == "1" else None)
            if termo is None:
                continue
            inicio = perf_counter()
            resultado = (mecanismo.buscar_palavra(termo) if opcao == "1"
                         else mecanismo.buscar_prefixo(termo))
            fim = perf_counter()
            if not resultado:
                print("Nenhum resultado encontrado.")
            elif opcao == "1":
                print(f"Encontrada em {len(resultado)} arquivo(s):")
                for nome in resultado:
                    print(f"- {nome}")
            else:
                print(f"Termos encontrados: {len(resultado)}")
                for palavra, arquivos in resultado.items():
                    print(f"- {palavra}: {', '.join(arquivos)}")
            mostrar_tempo(inicio, fim)
        else:
            print("Opção inválida.")


def main() -> int:
    try:
        stopwords = carregar_stopwords(RAIZ / "stopwords.txt")
    except (OSError, UnicodeError, ValueError) as erro:
        print(f"Não foi possível carregar stopwords.txt: {erro}")
        return 1
    trie, avisos = carregar_autocomplete(RAIZ / "palavras_iniciais.txt")
    mecanismo = MecanismoBusca.carregar_pasta(RAIZ / "documentos", stopwords)
    for aviso in avisos + mecanismo.avisos:
        print(f"Aviso: {aviso}")
    if not mecanismo.documentos:
        print("Nenhum documento processado. Adicione arquivos UTF-8 em documentos/ e reinicie.")
    while True:
        print("\nTRABALHO A1 — CAIO E MARIA")
        print("1 - Autocomplete (Parte I)\n2 - Busca em documentos (Parte II)\n3 - Sair")
        opcao = input("Escolha: ").strip()
        if opcao == "1":
            menu_autocomplete(trie)
        elif opcao == "2":
            menu_documentos(mecanismo, stopwords)
        elif opcao == "3":
            print("Programa encerrado.")
            return 0
        else:
            print("Opção inválida.")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (EOFError, KeyboardInterrupt):
        print("\nPrograma encerrado.")
