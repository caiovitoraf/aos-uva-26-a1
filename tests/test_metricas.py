"""Confere contagens conhecidas e a preservação dos resultados das consultas."""

import unittest

from indice_invertido import MecanismoBusca
from metricas import ContadorPassos, ordenar_com_passos
from trie import Trie


class TestContadorPassos(unittest.TestCase):
    def test_exata_cinco_caracteres_e_verificacao_final(self):
        trie = Trie()
        trie.inserir("dados")
        contador = ContadorPassos()
        self.assertTrue(trie.buscar("dados", contador))
        self.assertEqual(contador.etapas, {
            "Caracteres do caminho examinados": 5,
            "Finais de palavra verificados": 1,
        })
        self.assertEqual(contador.total, 6)
        # Uma consulta nova recebe um contador novo, sem herdar a anterior.
        outro = ContadorPassos()
        trie.buscar("dados", outro)
        self.assertEqual(outro.total, 6)

    def test_falha_conta_so_caminho_tentado(self):
        trie = Trie()
        trie.inserir("dados")
        contador = ContadorPassos()
        self.assertFalse(trie.buscar("dez", contador))
        self.assertEqual(contador.etapas, {"Caracteres do caminho examinados": 2})
        contador = ContadorPassos()
        self.assertFalse(trie.buscar("dado", contador))
        self.assertEqual(contador.total, 5)  # Quatro caracteres e fim de palavra.

    def test_insercao_nova_e_duplicata(self):
        trie = Trie()
        novo = ContadorPassos()
        self.assertTrue(trie.inserir("dados", novo))
        self.assertEqual(novo.total, 12)  # 5 caracteres + 5 nós + 1 final + 1 cadastro.
        repetido = ContadorPassos()
        self.assertFalse(trie.inserir("dados", repetido))
        self.assertEqual(repetido.total, 6)
        self.assertNotIn("Nós criados", repetido.etapas)
        self.assertNotIn("Palavras cadastradas", repetido.etapas)

    def test_prefixo_conta_descendentes_e_strings_de_saida(self):
        trie = Trie()
        for palavra in ["dados", "dança"]:
            trie.inserir(palavra)
        contador = ContadorPassos()
        self.assertEqual(trie.buscar_prefixo("da", contador), ["dados", "dança"])
        self.assertEqual(contador.etapas["Caracteres do caminho examinados"], 2)
        self.assertEqual(contador.etapas["Nós descendentes visitados"], 6)
        self.assertEqual(contador.etapas["Finais de palavra verificados"], 7)
        self.assertEqual(contador.etapas["Palavras recuperadas"], 2)
        self.assertEqual(contador.etapas["Caracteres copiados para sugestões"], 10)
        self.assertGreater(contador.etapas["Comparações entre textos na ordenação"], 0)
        contador = ContadorPassos()
        self.assertEqual(trie.buscar_prefixo("dados", contador), ["dados"])
        self.assertEqual(contador.total, 7)  # String do próprio prefixo é reaproveitada.

    def test_hash_conta_acesso_e_documentos_sem_simular_internos(self):
        mecanismo = MecanismoBusca()
        mecanismo.indice = {"dados": {"a.txt", "b.txt"}}
        contador = ContadorPassos()
        self.assertEqual(mecanismo.buscar_palavra("dados", contador), ["a.txt", "b.txt"])
        self.assertEqual(contador.etapas["Consultas ao índice Hash"], 1)
        self.assertEqual(contador.etapas["Documentos recuperados"], 2)
        self.assertGreater(contador.etapas["Comparações entre textos na ordenação"], 0)
        contador = ContadorPassos()
        self.assertEqual(mecanismo.buscar_palavra("ausente", contador), [])
        self.assertEqual(contador.etapas, {"Consultas ao índice Hash": 1})

    def test_prefixo_acumula_trie_e_hash_e_preserva_resultado(self):
        mecanismo = MecanismoBusca()
        mecanismo.indice = {"dados": {"a.txt", "b.txt"}, "dança": {"a.txt"}}
        for palavra in mecanismo.indice:
            mecanismo.trie.inserir(palavra)
        esperado = mecanismo.buscar_prefixo("da")
        contador = ContadorPassos()
        self.assertEqual(mecanismo.buscar_prefixo("da", contador), esperado)
        self.assertEqual(contador.etapas["Consultas ao índice Hash"], 2)
        self.assertEqual(contador.etapas["Documentos recuperados"], 3)
        self.assertEqual(contador.etapas["Palavras recuperadas"], 2)
        self.assertEqual(contador.total, sum(contador.etapas.values()))

    def test_ordenacao_conta_comparacoes_reais(self):
        contador = ContadorPassos()
        self.assertEqual(ordenar_com_passos(["b", "a"], contador), ["a", "b"])
        self.assertEqual(contador.total, 1)  # a < b é verdadeira; > não é executado.
        contador = ContadorPassos()
        self.assertEqual(ordenar_com_passos(["a", "b"], contador), ["a", "b"])
        self.assertEqual(contador.total, 2)  # b < a, depois b > a.
        self.assertEqual(ordenar_com_passos(["b", "a"], None), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
