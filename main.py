"""Interface de terminal das duas partes do trabalho. Execute: python main.py."""

from pathlib import Path
from time import perf_counter

from indice_invertido import MecanismoBusca
from metricas import ContadorPassos
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


def mostrar_medicao(inicio: float, fim: float, contador: ContadorPassos, operacao: str = "consulta") -> None:
    print(f"Tempo da {operacao}: {(fim - inicio) * 1000:.6f} ms")
    print(f"Passos contados (operações selecionadas): {contador.total}")
    for etapa, quantidade in contador.etapas.items():
        print(f"  - {etapa}: {quantidade}")


def menu_autocomplete(trie: Trie) -> None:
    print("\nAqui você testa sugestões usando um cadastro próprio de palavras.")
    print("Novas palavras ficam neste cadastro durante a sessão; elas não alteram os textos.")
    while True:
        print(f"\nPARTE I — DEMONSTRAÇÃO DE AUTOCOMPLETE — {trie.quantidade_palavras} palavras cadastradas")
        print("1 - Verificar se uma palavra está cadastrada\n2 - Ver sugestões pelo começo da palavra\n3 - Cadastrar palavra para testar o autocomplete\n4 - Voltar ao menu principal")
        opcao = input("Escolha: ").strip()
        if opcao == "4":
            return
        if opcao not in {"1", "2", "3"}:
            print("Opção inválida.")
            continue
        mensagens = {
            "1": "Digite a palavra inteira que deseja verificar: ",
            "2": "Digite o começo da palavra (prefixo), por exemplo prog: ",
            "3": "Digite a nova palavra para cadastrar nesta sessão: ",
        }
        termo = ler_termo(mensagens[opcao])
        if termo is None:
            continue
        contador = ContadorPassos()
        inicio = perf_counter()
        if opcao == "1":
            resultado = trie.buscar(termo, contador)
        elif opcao == "2":
            resultado = trie.buscar_prefixo(termo, contador)
        else:
            resultado = trie.inserir(termo, contador)
        fim = perf_counter()
        if opcao == "1":
            print("Palavra encontrada no cadastro." if resultado else "Palavra não encontrada no cadastro.")
        elif opcao == "2":
            print("Sugestões do cadastro:" if resultado else "Nenhuma palavra encontrada no cadastro com esse começo.")
            for palavra in resultado:
                print(f"- {palavra}")
        else:
            print("Palavra inserida no cadastro desta sessão." if resultado else "A palavra já estava cadastrada.")
        mostrar_medicao(inicio, fim, contador, "inserção" if opcao == "3" else "consulta")


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
    print("\nAqui você pesquisa as palavras extraídas dos arquivos da pasta documentos/.")
    print("Cada resultado mostra os arquivos em que a palavra aparece.")
    while True:
        print(f"\nPARTE II — BUSCA EM DOCUMENTOS — {len(mecanismo.documentos)} arquivos carregados")
        print("1 - Encontrar arquivos que contêm uma palavra\n2 - Encontrar palavras pelo começo e seus arquivos\n3 - Ver arquivos carregados\n4 - Ver contagens e tempos de processamento\n5 - Voltar ao menu principal")
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
            mensagem = ("Digite a palavra inteira que deseja encontrar nos textos: " if opcao == "1"
                        else "Digite o começo da palavra (prefixo), por exemplo comp: ")
            termo = ler_termo(mensagem, stopwords if opcao == "1" else None)
            if termo is None:
                continue
            contador = ContadorPassos()
            inicio = perf_counter()
            resultado = (mecanismo.buscar_palavra(termo, contador) if opcao == "1"
                         else mecanismo.buscar_prefixo(termo, contador))
            fim = perf_counter()
            if not resultado:
                print("Nenhum resultado encontrado.")
            elif opcao == "1":
                print(f"Encontrada em {len(resultado)} arquivo(s):")
                for nome in resultado:
                    print(f"- {nome}")
            else:
                print(f"Palavras dos textos que começam com '{termo}': {len(resultado)}")
                for palavra, arquivos in resultado.items():
                    print(f"- {palavra}: {', '.join(arquivos)}")
            mostrar_medicao(inicio, fim, contador)
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
        print("1 - Parte I: demonstração de autocomplete\n2 - Parte II: pesquisa nos documentos\n3 - Encerrar o programa")
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
