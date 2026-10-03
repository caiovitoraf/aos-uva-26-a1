"""Testes de comportamento, integração e navegação, sem dependências externas."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from indice_invertido import MecanismoBusca, descobrir_documentos
import main
from preprocessamento import carregar_stopwords, normalizar_termo, preprocessar, tokenizar
from trie import Trie

RAIZ = Path(__file__).resolve().parents[1]


class TestTrie(unittest.TestCase):
    def setUp(self):
        self.trie = Trie()
        self.palavras = ["programa", "programação", "programador", "computação", "computador", "complexidade"]
        for palavra in self.palavras:
            self.trie.inserir(palavra)

    def test_busca_exata_distingue_prefixo_e_fim(self):
        self.assertTrue(self.trie.buscar("programa"))
        self.assertTrue(self.trie.buscar("programação"))
        self.assertFalse(self.trie.buscar("prog"))
        self.assertFalse(self.trie.buscar("ausente"))
        self.assertFalse(self.trie.buscar(""))

    def test_prefixo_inclui_palavra_completa_e_descendentes(self):
        self.assertEqual(self.trie.buscar_prefixo("programa"), ["programa", "programador", "programação"])
        self.assertEqual(self.trie.buscar_prefixo("comp"), ["complexidade", "computador", "computação"])
        self.assertEqual(self.trie.buscar_prefixo("xyz"), [])

    def test_duplicatas_e_insercao_posterior(self):
        self.assertFalse(self.trie.inserir("programa"))
        self.assertEqual(self.trie.quantidade_palavras, 6)
        self.assertTrue(self.trie.inserir("processamento"))
        self.assertEqual(self.trie.buscar_prefixo("process"), ["processamento"])
        self.assertEqual(self.trie.quantidade_palavras, 7)

    def test_vazios_rejeitados_e_acentos_distintos(self):
        with self.assertRaises(ValueError):
            self.trie.inserir("")
        with self.assertRaises(ValueError):
            self.trie.buscar_prefixo("")
        self.assertFalse(self.trie.buscar("computacao"))

    def test_caminho_longo_sem_recursao(self):
        palavra = "a" * 2000
        self.trie.inserir(palavra)
        self.assertEqual(self.trie.buscar_prefixo("aaa"), [palavra])

    def test_resultados_conferidos_com_filtro_de_referencia(self):
        palavras = [f"{inicio}{meio}{fim}" for inicio in ["rede", "programa", "dado"]
                    for meio in ["dor", "ção", "s", ""] for fim in ["", "es", "mente"]]
        for palavra in palavras:
            self.trie.inserir(palavra)
        todas = set(self.palavras + palavras)
        for prefixo in ["r", "rede", "programa", "dad", "dadoção", "inexistente"]:
            self.assertEqual(self.trie.buscar_prefixo(prefixo), sorted(p for p in todas if p.startswith(prefixo)))


class TestPreprocessamento(unittest.TestCase):
    def test_pontuacao_e_simbolos_nao_juntam_palavras(self):
        self.assertEqual(tokenizar("DADOS,busca! rede-texto; índice+Hash / 10"),
                         ["dados", "busca", "rede", "texto", "índice", "hash", "10"])

    def test_unicode_equivalente_e_acentos_preservados(self):
        self.assertEqual(tokenizar("COMPUTAÇÃO computac\u0327a\u0303o computacao"),
                         ["computação", "computação", "computacao"])

    def test_exemplo_enunciado_e_duas_contagens(self):
        tokens, filtrados = preprocessar("Os Algoritmos de Busca são muito importantes.",
                                       {"os", "de", "são", "muito"})
        self.assertEqual(len(tokens), 7)
        self.assertEqual(filtrados, ["algoritmos", "busca", "importantes"])
        self.assertEqual(preprocessar("", set()), ([], []))

    def test_consulta_unica_e_stopwords(self):
        self.assertEqual(normalizar_termo(" DADOS! "), "dados")
        self.assertEqual(normalizar_termo("de"), "de")
        for texto in ["", "  ", "!!!", "dados busca", "dados-busca"]:
            with self.assertRaises(ValueError):
                normalizar_termo(texto)
        with self.assertRaises(ValueError):
            normalizar_termo("de", {"de"})

    def test_lista_stopwords_editavel_e_validada(self):
        with tempfile.TemporaryDirectory(prefix=".teste-", dir=RAIZ) as pasta:
            arquivo = Path(pasta) / "stopwords.txt"
            arquivo.write_text("# comentário\n\nOS\nde\n", encoding="utf-8")
            self.assertEqual(carregar_stopwords(arquivo), {"os", "de"})
            arquivo.write_text("duas palavras\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "linha 1"):
                carregar_stopwords(arquivo)


class TestIndice(unittest.TestCase):
    def setUp(self):
        self.temporaria = tempfile.TemporaryDirectory(prefix=".teste-", dir=RAIZ)
        self.addCleanup(self.temporaria.cleanup)
        self.pasta = Path(self.temporaria.name)
        (self.pasta / "a.txt").write_text("Os dados, dados! Computação busca.", encoding="utf-8")
        (self.pasta / "b.txt").write_text("Dados; computador. Desenvolvimento.", encoding="utf-8")
        self.mecanismo = MecanismoBusca.carregar_pasta(self.pasta, {"os"})

    def test_exata_documentos_sem_repeticoes(self):
        self.assertEqual(self.mecanismo.buscar_palavra("dados"), ["a.txt", "b.txt"])
        self.assertEqual(self.mecanismo.buscar_palavra("busca"), ["a.txt"])
        self.assertEqual(self.mecanismo.buscar_palavra("ausente"), [])
        self.assertEqual(self.mecanismo.buscar_palavra("os"), [])

    def test_prefixo_integra_trie_e_hash(self):
        self.assertEqual(self.mecanismo.buscar_prefixo("comp"),
                         {"computador": ["b.txt"], "computação": ["a.txt"]})
        self.assertEqual(self.mecanismo.buscar_prefixo("de"), {"desenvolvimento": ["b.txt"]})
        self.assertEqual(self.mecanismo.buscar_prefixo("xyz"), {})

    def test_estatisticas_e_todos_termos_na_trie(self):
        e = self.mecanismo.estatisticas()
        self.assertEqual((e["documentos"], e["tokens"], e["tokens_sem_stopwords"]), (2, 8, 7))
        self.assertEqual(e["termos_distintos"], 5)
        self.assertEqual(e["palavras_trie"], 5)
        for termo in self.mecanismo.indice:
            self.assertTrue(self.mecanismo.trie.buscar(termo))
        for nome in ["tempo_trie_s", "tempo_indice_s", "tempo_preprocessamento_s"]:
            self.assertGreaterEqual(e[nome], 0)

    def test_novo_arquivo_na_proxima_execucao_e_pasta_nao_recursiva(self):
        (self.pasta / "novo.TXT").write_text("novidade dados", encoding="utf-8")
        (self.pasta / "ignorar.md").write_text("ignorado", encoding="utf-8")
        (self.pasta / "subpasta").mkdir()
        (self.pasta / "subpasta" / "interno.txt").write_text("interno", encoding="utf-8")
        novo = MecanismoBusca.carregar_pasta(self.pasta, {"os"})
        self.assertEqual(novo.buscar_palavra("novidade"), ["novo.TXT"])
        self.assertEqual(len(novo.documentos), 3)
        self.assertEqual(novo.buscar_palavra("interno"), [])
        self.assertEqual(self.mecanismo.buscar_palavra("novidade"), [])

    def test_arquivo_vazio_e_codificacao_invalida(self):
        (self.pasta / "vazio.txt").write_text("", encoding="utf-8")
        (self.pasta / "ruim.txt").write_bytes(b"\xff\xfe\xff")
        novo = MecanismoBusca.carregar_pasta(self.pasta, {"os"})
        self.assertEqual(len(novo.documentos), 3)
        self.assertEqual(novo.documentos[-1].tokens, 0)
        self.assertEqual(len(novo.avisos), 1)
        self.assertIn("ruim.txt", novo.avisos[0])

    def test_erro_de_leitura_nao_interrompe_demais_documentos(self):
        original = Path.read_text
        def leitura(caminho, **kwargs):
            if caminho.name == "b.txt":
                raise PermissionError("acesso negado simulado")
            return original(caminho, **kwargs)
        with patch.object(Path, "read_text", leitura):
            novo = MecanismoBusca.carregar_pasta(self.pasta, {"os"})
        self.assertEqual(len(novo.documentos), 1)
        self.assertEqual(novo.buscar_palavra("dados"), ["a.txt"])
        self.assertIn("b.txt", novo.avisos[0])

    def test_pasta_vazia_e_inexistente(self):
        vazia = self.pasta / "vazia"
        vazia.mkdir()
        m = MecanismoBusca.carregar_pasta(vazia, set())
        self.assertEqual(m.estatisticas()["documentos"], 0)
        self.assertEqual(m.buscar_prefixo("a"), {})
        arquivos, avisos = descobrir_documentos(self.pasta / "inexistente")
        self.assertEqual(arquivos, [])
        self.assertTrue(avisos)

    def test_insercao_autocomplete_nao_contamina_documentos(self):
        trie = Trie()
        trie.inserir("exclusiva")
        self.assertTrue(trie.buscar("exclusiva"))
        self.assertFalse(self.mecanismo.trie.buscar("exclusiva"))


class TestInterface(unittest.TestCase):
    def executar_menu(self, funcao, entradas, *args):
        saida = io.StringIO()
        with patch("builtins.input", side_effect=entradas), redirect_stdout(saida):
            funcao(*args)
        return saida.getvalue()

    def test_autocomplete_insercao_consultas_e_entradas_invalidas(self):
        trie = Trie()
        saida = self.executar_menu(main.menu_autocomplete,
            ["9", "3", "Programação", "3", "programação", "1", "PROGRAMAÇÃO",
             "2", "prog", "1", "duas palavras", "2", "xyz", "4"], trie)
        self.assertEqual(trie.quantidade_palavras, 1)
        for esperado in ["Opção inválida", "Palavra inserida", "já estava cadastrada",
                         "Palavra encontrada", "- programação", "única palavra",
                         "Nenhuma palavra encontrada", "Tempo da consulta"]:
            self.assertIn(esperado, saida)

    def test_menu_documentos_consultas_listagem_estatisticas(self):
        m = MecanismoBusca()
        m.indice = {"desenvolvimento": {"a.txt"}, "dados": {"a.txt", "b.txt"}}
        for termo in m.indice:
            m.trie.inserir(termo)
        saida = self.executar_menu(main.menu_documentos,
            ["0", "1", "DADOS", "1", "de", "2", "de", "1", "xyz", "3", "4", "5"],
            m, {"de"})
        for esperado in ["Opção inválida", "Encontrada em 2 arquivo", "stopword",
                         "desenvolvimento: a.txt", "Nenhum resultado", "Nenhum documento",
                         "antes das stopwords", "Construção da Trie", "Tempo da consulta"]:
            self.assertIn(esperado, saida)

    def test_carregamento_palavras_iniciais_inexistentes(self):
        trie, avisos = main.carregar_autocomplete(RAIZ / "arquivo_inexistente.txt")
        self.assertEqual(trie.quantidade_palavras, 0)
        self.assertTrue(avisos)

    def test_stopwords_ausentes_falha_clara(self):
        with patch.object(main, "carregar_stopwords", side_effect=FileNotFoundError("ausente")):
            saida = io.StringIO()
            with redirect_stdout(saida):
                codigo = main.main()
        self.assertEqual(codigo, 1)
        self.assertIn("stopwords.txt", saida.getvalue())

    def test_programa_completo_iniciado_de_outro_diretorio(self):
        entradas = "9\n1\n1\ncomputador\n2\ncomp\n4\n2\n1\npacotes\n2\ncomp\n3\n4\n5\n3\n"
        resultado = subprocess.run([sys.executable, "-X", "utf8", str(RAIZ / "main.py")],
            input=entradas, text=True, encoding="utf-8", capture_output=True,
            cwd=RAIZ.parent, timeout=30)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        for esperado in ["AUTOCOMPLETE", "BUSCA EM DOCUMENTOS", "Palavra encontrada",
                         "redes.txt", "Documentos processados: 5", "Programa encerrado"]:
            self.assertIn(esperado, resultado.stdout)

    def test_eof_encerra_sem_traceback(self):
        resultado = subprocess.run([sys.executable, "-X", "utf8", str(RAIZ / "main.py")],
            input="", text=True, encoding="utf-8", capture_output=True, cwd=RAIZ, timeout=30)
        self.assertEqual(resultado.returncode, 0)
        self.assertIn("Programa encerrado", resultado.stdout)


class TestBaseEntregue(unittest.TestCase):
    def test_textos_tamanho_e_consistencia(self):
        stopwords = carregar_stopwords(RAIZ / "stopwords.txt")
        m = MecanismoBusca.carregar_pasta(RAIZ / "documentos", stopwords)
        self.assertEqual(len(m.documentos), 5)
        self.assertEqual(m.avisos, [])
        for doc in m.documentos:
            self.assertGreaterEqual(doc.tokens, 600, doc.nome)
            self.assertLessEqual(doc.tokens, 1000, doc.nome)
        self.assertEqual(m.trie.quantidade_palavras, len(m.indice))
        self.assertEqual(m.buscar_palavra("pacotes"), ["redes.txt"])
        self.assertEqual(m.buscar_palavra("transação"), ["banco_dados.txt"])
        self.assertEqual(len(m.buscar_palavra("dados")), 5)
        # A referência independente reconstrói o índice diretamente dos textos.
        referencia = {}
        for arquivo in sorted((RAIZ / "documentos").glob("*.txt")):
            _, tokens = preprocessar(arquivo.read_text(encoding="utf-8"), stopwords)
            for termo in tokens:
                referencia.setdefault(termo, set()).add(arquivo.name)
        self.assertEqual(m.indice, referencia)
        self.assertEqual(m.buscar_prefixo("comp"),
                         {t: sorted(referencia[t]) for t in sorted(referencia) if t.startswith("comp")})


if __name__ == "__main__":
    unittest.main()
