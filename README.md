# Trabalho A1 — Caio e Maria

Projeto de **Processamento e Busca de Textos**, da disciplina Análise e Otimização de Sistemas, Universidade Veiga de Almeida, professor André Lucio.

Implementa as duas partes obrigatórias: autocomplete com Trie própria e busca em arquivos usando a mesma classe Trie, vocabulário, índice invertido e Hash. O relatório está em [RELATORIO.md](RELATORIO.md). O PDF será preparado no momento da entrega.

## Requisitos e execução

Python **3.10 ou superior**, sem instalar bibliotecas. Validado com Python 3.12.14 no Windows. Abra um terminal nesta pasta e execute:

```console
python main.py
```

No Windows com o lançador Python instalado, também é possível usar `py -3 main.py`. Neste computador, o Python disponível é o runtime do Codex. No PowerShell, a partir da pasta do projeto, o comando confirmado é:

```powershell
& "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" -X utf8 main.py
```

Se o terminal apresentar problemas de acentuação, execute `python -X utf8 main.py` em um terminal com suporte a UTF-8. O programa lê seus arquivos em UTF-8 e aceita BOM. Para iniciar a partir de outra pasta, informe o caminho completo de `main.py`: as entradas são localizadas em relação ao arquivo do programa.

O menu principal oferece:

1. **Parte I: demonstração de autocomplete.** Permite verificar se uma palavra está cadastrada, ver sugestões pelo começo da palavra e cadastrar uma nova palavra para testar. O cadastro inicia com `palavras_iniciais.txt`; novas inserções valem durante a sessão.
2. **Parte II: pesquisa nos documentos.** Permite encontrar arquivos que contêm uma palavra, encontrar palavras pelo começo e seus respectivos arquivos, ver arquivos carregados e consultar contagens e tempos de processamento. As palavras vêm dos textos de `documentos/`.
3. **Encerrar o programa.** Dentro de cada parte, a opção **Voltar ao menu principal** permite escolher outra parte sem encerrar a sessão.

**Por que cadastrar uma palavra na Parte I?** Essa parte demonstra o autocomplete exigido pelo trabalho. Ao cadastrar `programável`, digitar o começo `prog` passa a incluí-la nas sugestões. Isso não acrescenta a palavra aos textos: a Parte II encontra `programável` somente se ela estiver em algum arquivo. As duas partes compartilham a implementação da Trie, com instâncias independentes.

**Palavra inteira ou começo?** Verificar `programação` procura exatamente essa palavra. Informar `prog` como começo (prefixo) retorna palavras maiores, como `programa`, `programador` e `programação`. Os campos de entrada indicam qual das duas formas deve ser digitada.

## Organização

```text
a1-caio-maria/
├── main.py                    # Menus e apresentação
├── trie.py                    # Nós, inserção e buscas da Trie
├── preprocessamento.py        # Unicode, tokens e stopwords
├── indice_invertido.py        # Leitura, Hash, vocabulário e integração
├── metricas.py                 # Contador e ordenação com comparações contadas
├── experimento.py             # Medições com 1, 3 e 5 documentos
├── palavras_iniciais.txt       # Uma palavra por linha para a Parte I
├── stopwords.txt               # Lista editável, uma palavra por linha
├── documentos/                # Cinco textos originais sobre computação
├── tests/                     # Testes do projeto e das métricas
├── evidencias/medicoes.json    # Amostras, medianas, hashes e resultados
├── evidencias/demonstracao.txt # Entradas e saída real de uma sessão
├── evidencias/testes.txt       # Resultado da execução dos 33 testes
├── README.md
└── RELATORIO.md
```

## Regras de entrada e consultas

- Todos os arquivos `.txt` diretamente em `documentos/` são descobertos automaticamente, inclusive extensões `.TXT`. Subpastas não são percorridas. Os nomes não estão fixados no código da aplicação.
- Adicione, altere ou remova textos em UTF-8 e reinicie o programa para reconstruir a base. Não há atualização automática durante uma sessão.
- Textos e consultas são convertidos para minúsculas e normalizados em Unicode NFC. Pontuação e símbolos viram separadores; letras, números e marcas Unicode são preservados.
- Acentos são preservados: `computação` e `computacao` são chaves diferentes. Os dois termos ocorrem nesta base porque alguns textos discutem essa diferença.
- Cada consulta aceita **uma palavra ou um prefixo não vazio**. `DADOS!` vira `dados`; `dados-busca` gera dois tokens e é rejeitado como consulta.
- As stopwords são retiradas apenas da indexação dos documentos. Consultar uma stopword exata explica a ausência no índice. Um prefixo como `de` continua válido e pode encontrar `desenvolvimento`.
- O autocomplete permite palavras que também seriam stopwords e inicia com 26 palavras. Novas inserções ficam disponíveis durante a sessão, sem gravação em disco. Duplicatas não aumentam a contagem.
- Sugestões e nomes de arquivos são ordenados pela ordem de strings do Python, que não é uma ordenação linguística específica do português.
- Arquivos ilegíveis são ignorados com aviso; arquivos vazios contam como processados, com zero tokens. Falha na leitura ou validação de `stopwords.txt` encerra com uma mensagem de erro.

## Exemplos para conferir

| Parte | Consulta | Resultado esperado na base entregue |
| --- | --- | --- |
| I — prefixo | `comp` | compilador, complexidade, computacional, computador, computação |
| I — exata | `prog` | Não encontrada; é caminho, mas não palavra cadastrada |
| I — inserção | `programável` | Disponível para novas consultas na mesma sessão |
| II — exata | `pacotes` | redes.txt |
| II — exata | `transação` | banco_dados.txt |
| II — exata | `dados` | Os cinco documentos |
| II — prefixo | `comp` | 26 termos, cada um com seus respectivos arquivos |
| II — exata | `zzzinexistente` | Nenhum resultado |

Confira a sessão completa em [evidencias/demonstracao.txt](evidencias/demonstracao.txt). A digitação das entradas está registrada no início do arquivo, pois o subprocesso não ecoa automaticamente o que foi fornecido.

Na base entregue, as estatísticas são: **5 documentos, 3.850 tokens antes das stopwords, 2.488 depois, 1.022 termos distintos e 1.022 palavras na Trie dos documentos**. Tempos variam a cada execução.

## Contador de passos junto ao tempo

Cada consulta e inserção feita pelos menus usa um contador novo. A tela apresenta o tempo, o total de **operações selecionadas** e o detalhamento. Por exemplo, buscar `dados` no cadastro percorre cinco caracteres e verifica uma marca de fim de palavra: **6 passos contados**.

| Etapa contada | Unidade adotada |
| --- | --- |
| Caracteres da palavra/caminho examinados | Um por caractere tentado na Trie, inclusive a tentativa que falha |
| Nós criados | Um por novo nó durante uma inserção |
| Finais de palavra verificados | Um por marca de fim examinada |
| Palavras cadastradas ou recuperadas | Um por cadastro novo ou sugestão obtida |
| Nós descendentes visitados | Um por descendente explorado na busca por prefixo |
| Caracteres copiados para sugestões | Um por caractere copiado ao montar uma nova string de resultado |
| Consultas ao índice Hash | Um por chamada de acesso ao índice para um termo |
| Documentos recuperados | Um por associação termo-documento retornada |
| Comparações entre textos na ordenação | Uma por operação `<` ou `>` entre strings executada pelo comparador |

O total soma unidades do modelo escolhido; não representa todas as instruções do Python nem ciclos de processador. A comparação entre strings conta como uma operação aqui, embora possa comparar vários caracteres internamente. Colisões, hashing e outros mecanismos internos de `dict`, alocações, controle da pilha, normalização da entrada e impressão não são contados. Na busca por prefixo, a mesma métrica acumula a Trie e os documentos de cada sugestão; um arquivo associado a duas palavras conta duas associações.

O tempo mostrado nos menus inclui o trabalho do contador e do comparador instrumentado, mas exclui a digitação, a normalização e a impressão. Portanto, não é diretamente comparável ao tempo sem instrumentação. A API mantém o contador opcional; `experimento.py` continua medindo sem contador. As medianas originais do relatório estão identificadas como a execução anterior à inclusão da instrumentação.

Uma busca exata que alcança todos os m caracteres na Trie conta `T_contado(m) = m + 1`: caracteres examinados e verificação final. Isso é um modelo de custo da busca, não uma fórmula de tempo em segundos. Uma falha antecipada conta apenas o caminho efetivamente tentado. Prefixos e resultados maiores acrescentam outras etapas. As comparações de ordenação podem variar com a ordem inicial de enumeração dos conjuntos e dos caminhos; não existe um total fixo universal para toda consulta do mesmo tamanho.

## Testes e medições

```console
python -m unittest discover -s tests -v
python experimento.py --repeticoes 15
```

Para usar o runtime local, substitua `python` pelo comando PowerShell do início, mantendo os argumentos. Não é necessário `pip install`.

Os 33 testes verificam Trie, pré-processamento, consultas, contagens, arquivos vazios e ilegíveis, inclusão automática de documento, independência entre instâncias e navegação nos menus. O resultado da execução está em [evidencias/testes.txt](evidencias/testes.txt). Os textos também são conferidos quanto ao tamanho, entre 600 e 1.000 tokens cada. Execute os testes de referência antes de personalizar a base: algumas verificações descrevem os cinco textos entregues.

O experimento usa os primeiros 1, 3 e 5 arquivos em ordem de nome, faz um aquecimento e registra a mediana de 15 execuções por subconjunto. Os nomes são descobertos na pasta. A leitura e a apresentação ficam fora dos tempos de construção; as consultas incluem recuperação e ordenação, mas não a impressão. As amostras individuais e hashes SHA-256 das entradas são gravados em `evidencias/medicoes.json`, substituindo a medição anterior.

Ao mudar os textos ou as stopwords, gere novas evidências e atualize os exemplos e tabelas do relatório. A demonstração entregue representa a versão inicial; uma nova sessão pode ser registrada separadamente. Amostras pequenas não provam uma classe de complexidade.

## Limites e entrega

Não há KMP, busca por frases, ranking, stemming, lematização, persistência de índices nem Trie comprimida. O índice armazena presença em documentos, sem frequência ou posição. Os textos são originais e preparados para testes acadêmicos, sem uso de respostas de colegas.

Antes da entrega, revisar o código e as explicações com Caio e Maria, confirmar os dados acadêmicos exigidos pelo professor e converter o relatório revisado para PDF nesta mesma pasta. Nenhum prazo ou número de matrícula foi presumido.

## Compartilhamento no GitHub

Este projeto está no repositório público [aos-uva-26-a1](https://github.com/caiovitoraf/aos-uva-26-a1). Para obter uma cópia e executar:

```console
git clone https://github.com/caiovitoraf/aos-uva-26-a1.git
cd aos-uva-26-a1
python main.py
```

A publicação contém somente o projeto preparado para Caio e Maria. Enunciados, slides, cadernos e trabalhos de colegas não fazem parte deste repositório. A pasta local `a1-caio-maria` é um repositório Git independente. Faça commits e pushes diretamente nela.
