"""Gera medições repetíveis e exemplos reais para o relatório, em JSON."""

import argparse
import hashlib
import json
from pathlib import Path
import platform
from statistics import median
from time import perf_counter

from indice_invertido import MecanismoBusca, descobrir_documentos
from preprocessamento import carregar_stopwords

RAIZ = Path(__file__).resolve().parent


def executar(repeticoes: int) -> dict:
    stopwords = carregar_stopwords(RAIZ / "stopwords.txt")
    arquivos, avisos = descobrir_documentos(RAIZ / "documentos")
    if avisos or len(arquivos) < 5:
        raise ValueError("O experimento requer pelo menos cinco documentos legíveis na pasta.")
    grupos = []
    for quantidade in (1, 3, 5):
        selecionados = arquivos[:quantidade]
        aquecimento = MecanismoBusca.construir(selecionados, stopwords)
        if aquecimento.avisos:
            raise ValueError("; ".join(aquecimento.avisos))
        amostras = []
        for _ in range(repeticoes):
            mecanismo = MecanismoBusca.construir(selecionados, stopwords)
            if mecanismo.avisos:
                raise ValueError("; ".join(mecanismo.avisos))
            amostra = mecanismo.estatisticas()
            for nome, consulta, termo in [("consulta_dados_s", mecanismo.buscar_palavra, "dados"),
                                          ("consulta_comp_s", mecanismo.buscar_prefixo, "comp")]:
                inicio = perf_counter()
                consulta(termo)
                amostra[nome] = perf_counter() - inicio
            amostras.append(amostra)
        tempos = [chave for chave in amostras[0] if chave.endswith("_s")]
        grupos.append({
            "arquivos": [p.name for p in selecionados],
            "contagens": {k: v for k, v in amostras[0].items() if not k.endswith("_s")},
            "medianas_ms": {k.removesuffix("_s"): median(a[k] for a in amostras) * 1000 for k in tempos},
            "amostras": amostras,
        })
    completo = MecanismoBusca.construir(arquivos, stopwords)
    if completo.avisos:
        raise ValueError("; ".join(completo.avisos))
    return {
        "python": platform.python_version(),
        "sistema": platform.system(),
        "repeticoes": repeticoes,
        "metodo": "Um aquecimento por subconjunto; mediana de execuções; consultas sem impressão; leitura fora dos tempos de construção.",
        "sha256_documentos": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in arquivos},
        "sha256_stopwords": hashlib.sha256((RAIZ / "stopwords.txt").read_bytes()).hexdigest(),
        "documentos": [{"nome": d.nome, "tokens": d.tokens, "tokens_sem_stopwords": d.tokens_sem_stopwords}
                       for d in completo.documentos],
        "subconjuntos": grupos,
        "exemplos": {
            "dados": completo.buscar_palavra("dados"),
            "pacotes": completo.buscar_palavra("pacotes"),
            "transação": completo.buscar_palavra("transação"),
            "computação": completo.buscar_palavra("computação"),
            "computacao": completo.buscar_palavra("computacao"),
            "zzzinexistente": completo.buscar_palavra("zzzinexistente"),
            "prefixo_comp": completo.buscar_prefixo("comp"),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeticoes", type=int, default=15)
    args = parser.parse_args()
    if args.repeticoes < 3:
        parser.error("Use pelo menos três repetições.")
    try:
        resultado = executar(args.repeticoes)
    except (OSError, UnicodeError, ValueError) as erro:
        parser.exit(1, f"Erro no experimento: {erro}\n")
    destino = RAIZ / "evidencias" / "medicoes.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Evidências gravadas em: {destino}")
    for grupo in resultado["subconjuntos"]:
        print(f"{grupo['contagens']['documentos']} documentos: {grupo['contagens']}; medianas (ms): {grupo['medianas_ms']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
