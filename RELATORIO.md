# Relatório técnico — Processamento e Busca de Textos

**Trabalho A1 — Caio e Maria**

Universidade Veiga de Almeida — Análise e Otimização de Sistemas

Professor: André Lucio

## 1. Objetivo e organização da solução

O projeto integra uma Trie própria para autocomplete e um mecanismo de busca em arquivos de texto. A mesma classe Trie é reutilizada nas duas partes, em instâncias independentes. A primeira recebe palavras de um arquivo inicial e aceita inserções durante a execução. A segunda contém exclusivamente o vocabulário extraído dos documentos. Assim, inserir uma palavra no autocomplete não atribui sua presença a arquivos que não a contêm.

O código usa Python e apenas sua biblioteca padrão. Os módulos separam Trie, pré-processamento, indexação e interface de terminal. O `dict` implementa a estrutura Hash permitida pelo enunciado; não são utilizadas bibliotecas prontas de Trie, índice invertido ou mecanismo de busca. Todos os arquivos `.txt` diretamente na pasta de documentos são descobertos a cada início, sem nomes fixados no código da aplicação.

## 2. Trie, autocomplete e integração

Cada nó da Trie contém um dicionário de filhos, identificado pelo próximo caractere, e uma marca de fim de palavra. Inserir `programa` percorre ou cria seus caracteres e marca seu último nó. Inserir `programação` reaproveita o caminho inicial e continua por novos nós. Buscar `prog` não encontra uma palavra exata, embora esse caminho exista. Inserir novamente uma palavra já marcada não altera a contagem.

A busca por prefixo percorre os caracteres informados. Se encontrar o caminho, visita os descendentes em profundidade, monta as palavras completas e ordena os resultados. A visita usa uma pilha explícita e um caminho mutável: evita depender do limite de recursão do Python e evita copiar strings em todos os nós intermediários. As palavras são montadas apenas nos nós que representam finais válidos.

Na Parte II, cada palavra obtida pela Trie é consultada no índice invertido. O resultado relaciona **cada termo** a seus arquivos, preservando a integração exigida: `prefixo → termos na Trie → documentos no índice/Hash`.

## 3. Pré-processamento, vocabulário e Hash

O texto é normalizado em Unicode NFC, convertido para minúsculas e novamente normalizado. Pontuação, símbolos e espaços se tornam separadores; letras, números e marcas Unicode são preservados. A tokenização divide o resultado pelos separadores. Por fim, são retiradas as palavras presentes na lista editável de stopwords. Por exemplo, `Os Algoritmos de Busca são muito importantes.` gera sete tokens; a filtragem deixa `algoritmos`, `busca` e `importantes`.

Substituir pontuação por espaços evita transformar `dados,busca` em `dadosbusca`. Acentos são preservados: `computação` e `computacao` permanecem distintos. Consultas usam a mesma normalização. Uma consulta precisa produzir um único token; frases e entradas vazias são rejeitadas. Stopwords exatas recebem uma explicação, mas um prefixo igual a uma stopword continua válido para encontrar palavras maiores.

O índice possui o formato `dict[str, set[str]]`: a chave é um termo, e o valor é o conjunto de nomes de documentos. Repetições de uma palavra no mesmo arquivo não duplicam seu nome. As chaves distintas constituem o vocabulário, inserido na Trie. A estrutura é chamada de **índice invertido** porque transforma a relação original “documento contém palavras” em “palavra ocorre nestes documentos”.

Uma função hash calcula, a partir da chave, um valor que auxilia sua localização na tabela. Chaves diferentes podem produzir colisões; a estrutura precisa resolver essas disputas e comparar as chaves, mantendo as associações corretas. O `dict` cuida desses mecanismos. O acesso tem custo médio O(1) em relação ao número de entradas sob condições usuais; esse modelo não elimina o processamento dos caracteres da chave nem o custo de devolver os resultados. Um pior caso de colisões pode exigir percorrer várias entradas.

## 4. Análise de complexidade

As variáveis utilizadas são: **m**, tamanho de uma palavra; **p**, tamanho do prefixo; **C**, total de caracteres nos textos; **H**, total de caracteres dos tokens filtrados, incluindo repetições; **V**, termos distintos; **S**, soma dos tamanhos desses termos; **A**, associações distintas entre termos e documentos. Em uma busca por prefixo, **n** é o número de nós visitados abaixo dele, **k** é o número de palavras retornadas e **R** é a soma dos tamanhos dessas palavras. Para ordenações, **L** limita o tamanho dos termos e **f** limita o tamanho dos nomes dos arquivos; **d** é a quantidade de documentos retornados para um termo.

| Operação | Custo e justificativa |
| --- | --- |
| Inserção na Trie | O(m) médio, percorrendo caracteres com acesso médio constante aos filhos. |
| Busca exata na Trie | O(m) médio; a marca de fim distingue palavra de prefixo. |
| Busca por prefixo na Trie | O(p + n + R) antes de ordenar: localizar caminho, visitar descendentes e materializar strings. A ordenação acrescenta até O(k log k · L) para k ≥ 2. |
| Pré-processamento | O(C) neste processamento: percorrer caracteres, gerar tokens e consultar stopwords em conjunto, com acesso médio constante após hashing. |
| Construção do índice | O(H + A) médio, incluindo criação dos conjuntos de termos por arquivo, hashing dos tokens e armazenamento das associações. Não inclui leitura e tokenização. |
| Construção da Trie do vocabulário | O(S) médio; o custo depende dos caracteres, não apenas da quantidade V. |
| Busca exata em documentos | O(m + d + d log d · f) médio para d ≥ 2: hashing da chave, recuperação e ordenação dos nomes. Com zero ou um resultado, não há custo de ordenação logarítmica. |
| Busca por prefixo em documentos | Custo da busca na Trie, mais as consultas Hash e a recuperação/ordenação dos arquivos de cada termo. Se dᵢ é a quantidade de arquivos do termo i, somam-se os custos de saída e ordenação correspondentes. |

Esses custos de construção usam o modelo médio de tabelas Hash; não são garantias para uma distribuição adversa de colisões. Strings iguais podem exigir comparação de caracteres. Os limites com L e f tornam explícito que comparar strings não é sempre uma operação unitária. Um termo recuperado pela Trie também precisa ser processado como chave; a soma desse custo está limitada pelo volume R já considerado.

A memória persistente das estruturas é O(S + A + D), em que D é a quantidade de documentos: nós e transições da Trie, chaves do índice, associações e metadados. O processamento mantém temporariamente o conteúdo, os tokens e o conjunto de termos do arquivo atual. Não conserva o texto integral de todos os arquivos em memória. Objetos e dicionários por nó acrescentam um custo prático considerável, mesmo com compartilhamento de prefixos.

## 5. Base, exemplos e medições

Foram preparados cinco textos originais, com temas de computação e termos compartilhados. As contagens incluem títulos, números e tokens de exemplo que aparecem nos textos. A base não é um corpus externo representativo de todas as aplicações.

| Documento | Tokens antes das stopwords | Tokens depois |
| --- | ---: | ---: |
| algoritmos.txt | 752 | 490 |
| banco_dados.txt | 781 | 514 |
| engenharia_software.txt | 779 | 494 |
| inteligencia_artificial.txt | 767 | 498 |
| redes.txt | 771 | 492 |
| **Total** | **3.850** | **2.488** |

O vocabulário contém **1.022 termos distintos**, também correspondentes às **1.022 palavras na Trie dos documentos**. A Trie independente do autocomplete começa com 26 palavras.

Consultas executadas na versão entregue:

- Autocomplete, prefixo `comp`: `compilador`, `complexidade`, `computacional`, `computador`, `computação`.
- Autocomplete, inserção de `programável`: a busca subsequente por `PROGRAMÁVEL` encontra a palavra; nova inserção não aumenta a contagem. A busca exata por `prog` não encontra palavra cadastrada.
- Documentos, `pacotes`: somente `redes.txt`; `transação`: somente `banco_dados.txt`; `dados`: os cinco arquivos; `zzzinexistente`: nenhum resultado.
- Documentos, prefixo `comp`: **26 termos**. Entre eles, `comparação` aparece em `banco_dados.txt`; `complexidades` em `engenharia_software.txt`; `computadores` em `redes.txt`; `compilador` aparece nos cinco. A lista integral com as associações está nas evidências.

Os textos mencionam explicitamente `comp` e `computacao`, que também entram no índice. `computacao` aparece em três documentos; `computação` aparece nos cinco. Isso confirma que a normalização preserva acentos e que a indexação considera todas as ocorrências, incluindo exemplos sobre o próprio sistema.

O experimento usou Python 3.12.14 no Windows, com os primeiros 1, 3 e 5 arquivos em ordem alfabética. O grupo de três contém algoritmos, banco de dados e engenharia de software. Houve um aquecimento por grupo e 15 repetições; a tabela apresenta medianas em milissegundos. A leitura fica fora dos tempos de construção; a consulta inclui recuperar e ordenar resultados, excluindo impressão e entrada do usuário.

| Documentos | Tokens | Termos | Pré-processamento (ms) | Índice (ms) | Trie (ms) | Exata `dados` (ms) | Prefixo `comp` (ms) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 752 | 342 | 0,4543 | 0,0694 | 0,5474 | 0,0015 | 0,0273 |
| 3 | 2.312 | 727 | 1,3792 | 0,2653 | 1,3030 | 0,0019 | 0,0388 |
| 5 | 3.850 | 1.022 | 2,3482 | 0,4456 | 2,0652 | 0,0031 | 0,0570 |

Nesta execução, o pré-processamento cresceu aproximadamente com o volume de texto. A Trie acompanhou o crescimento do vocabulário e de seus caracteres. A consulta por prefixo teve custo maior que a exata, pois materializou várias palavras e suas associações. A exata também retornou mais arquivos nos grupos maiores; sua duração não mede somente o acesso Hash. São observações compatíveis com os custos descritos, sem provar as classes assintóticas. Tempos pequenos variam conforme computador, cache, alocação e outros processos; a ordem fixa dos grupos também limita a interpretação experimental.

[medicoes.json](evidencias/medicoes.json) guarda todas as amostras, contagens, hashes das entradas e exemplos. [demonstracao.txt](evidencias/demonstracao.txt) guarda entradas e a saída real de uma sessão. Alterações na base exigem novas medições e atualização deste relatório.

## 6. Respostas às questões conceituais da Parte I

1. **Por que uma Trie é adequada para autocomplete?** O prefixo aponta diretamente para um caminho; somente seus descendentes precisam ser explorados para obter sugestões. Não é necessário comparar o prefixo com todas as palavras do vocabulário.
2. **Qual a vantagem sobre busca sequencial?** Uma lista sem índice pode exigir examinar todas as palavras, com custo dependente de sua quantidade e dos caracteres comparados. A Trie localiza o caminho em função do comprimento do prefixo e depois trabalha sobre o subconjunto correspondente. Ainda existe custo para devolver as sugestões.
3. **Como prefixos comuns são representados?** São compartilhados nos mesmos nós e arestas iniciais. `programa` e `programação` seguem o mesmo caminho inicial; a marca de fim permite terminar uma palavra e continuar até outra.
4. **Qual a complexidade de buscar uma palavra de tamanho m?** O(m) no modelo médio desta implementação, com acesso aos filhos por dicionário. São percorridos até m caracteres e verificada a marca de fim.
5. **Qual problema de memória pode ocorrer?** Cada caractere novo pode criar um nó com um dicionário, referências e marca de fim. Muitas palavras com pouco compartilhamento produzem muitos nós; o custo dos objetos pode superar o espaço ocupado apenas pelas strings.
6. **O que é uma Trie comprimida?** É uma variante que pode reunir trechos de caminhos sem ramificação em arestas rotuladas por sequências de caracteres. Reduz nós e referências intermediárias, mas exige comparar trechos e dividir arestas em determinadas inserções. Foi discutida conceitualmente, sem implementação neste projeto.

## 7. Validação, limitações e fonte

Os **26 testes automatizados passaram**. Eles verificam busca exata versus prefixo, duplicatas, inserções, Unicode, stopwords, contagens, integração Trie/índice, descoberta de novo arquivo na execução seguinte, arquivos vazios e ilegíveis, menus e execução a partir de outra pasta. Uma palavra de 2.000 caracteres também confirma que a busca por prefixo não depende de recursão.

A solução não inclui busca por frases, ranking, frequências, posições, correção ortográfica, remoção de acentos, stemming, lematização nem KMP. Os índices são reconstruídos ao iniciar; arquivos adicionados durante a sessão entram apenas na próxima execução. A lista de stopwords é simples e pode remover informação relevante em alguns contextos. A ordenação segue strings Unicode, sem regras linguísticas específicas do português. A Trie tradicional e a preparação integral da base podem consumir memória significativa em coleções grandes.

**Fonte de requisitos:** enunciado local *Trabalho Prático - A1 - Unidade_2_Processamento_Textos.docx*, professor André Lucio, lido em 03/10/2026. Textos de teste, decisões, respostas e análise foram preparados para esta implementação; não constituem gabarito oficial. Código e relatório devem ser revisados pelos integrantes antes da entrega. Prazo, matrículas e exigências adicionais não foram presumidos. A conversão para PDF está reservada ao momento da entrega.
