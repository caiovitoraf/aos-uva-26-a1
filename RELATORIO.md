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

### 4.1. Notações e variáveis

**T_contado** representa a soma das operações selecionadas que o programa registra em uma execução. Não é tempo em segundos nem contagem de todas as instruções do Python. **O(g)** descreve um limite superior para o crescimento do custo, usando uma função de referência g. Por exemplo, se `T_contado(m) = m + 1`, então `m + 1 ≤ 2m` para `m ≥ 1`: o custo contado é limitado por uma constante vezes m e pertence a O(m). Essa simplificação serve para comparar crescimento; não transforma seis passos em cinco nem substitui a contagem observada. Para uma variável de entrada x, a definição exige constantes c₀ > 0 e x₀ tais que `T(x) ≤ c₀·g(x)` para todo `x ≥ x₀`. No exemplo, `c₀ = 2`, `x₀ = 1` e `g(m) = m`; essas constantes justificam o limite e não são parcelas adicionadas pelo contador.

As variáveis das consultas são:

| Símbolo | Significado |
| --- | --- |
| m | Número de caracteres da palavra pesquisada ou inserida |
| p | Número de caracteres do prefixo |
| r | Caracteres efetivamente tentados antes de uma falha no caminho |
| u | Novos nós criados em uma inserção, entre zero e m |
| b | Indicador: 1 quando uma nova palavra é cadastrada; 0 quando já existia |
| n | Nós descendentes visitados depois de localizar o prefixo, excluindo seu próprio nó |
| k | Palavras retornadas pelo prefixo |
| B | Caracteres copiados ao montar novas strings de sugestões; não inclui o próprio prefixo quando ele já é uma palavra e sua string é reaproveitada |
| R | Soma dos tamanhos de todas as palavras retornadas; B ≤ R |
| q | Comparações `<` e `>` executadas ao ordenar as palavras sugeridas |
| d, q_d | Documentos de uma consulta exata e comparações executadas para ordená-los |
| dᵢ, qᵢ | Documentos e comparações de ordenação para a i-ésima palavra de um prefixo |
| L, f | Limites para o tamanho das palavras e dos nomes de arquivos nas comparações |

`Σᵢ` indica somar as parcelas de cada palavra retornada. Se duas palavras aparecem em dois e três documentos, `Σᵢ dᵢ = 2 + 3 = 5`: são associações, mesmo que um arquivo apareça nos dois grupos. `log` indica logaritmo; nas expressões de ordenação, pode-se adotar base 2. A base altera constantes, sem mudar a classe de crescimento. Para listas de zero ou um elemento, as parcelas de ordenação são consideradas zero.

### 4.2. Modelo de contagem de passos

Cada consulta ou inserção recebe um contador novo. O total é a soma das parcelas abaixo; as etapas são mostradas separadamente para permitir sua interpretação.

| Operação selecionada | Como é contada |
| --- | --- |
| Examinar caractere da palavra ou caminho | Um passo por caractere tentado, inclusive o que causa a falha |
| Criar nó | Um passo por nó novo na inserção |
| Verificar fim de palavra | Um passo por marca de fim examinada |
| Cadastrar palavra | Um passo quando a inserção é nova |
| Visitar descendente | Um passo por nó descendente explorado na busca por prefixo |
| Recuperar sugestão | Um passo por palavra retornada |
| Copiar caracteres de sugestão | Um passo por caractere copiado ao criar a string com `join` |
| Consultar índice Hash | Um passo por chamada ao `dict` para localizar um termo |
| Recuperar documento | Um passo por associação termo-documento retornada |
| Comparar textos para ordenar | Um passo por comparação `<` ou `>` executada pelo comparador |

Esse é um modelo explícito de operações selecionadas, não uma contagem linha a linha. Não conta controle de laços e pilha, alocações, todas as instruções de acesso aos filhos, normalização, entrada ou impressão. A comparação entre strings conta uma operação, embora possa comparar vários caracteres internamente. Hashing e tratamento de colisões internos do `dict` não são observados. Essas diferenças são consideradas na análise assintótica, sem atribuir ao contador trabalho que ele não registra.

O tempo apresentado nos menus inclui a instrumentação. Os totais de comparações podem variar conforme a ordem inicial de enumeração dos conjuntos e caminhos. A sequência de resultados ordenados permanece igual, mas não existe uma fórmula numérica fixa de comparações para toda entrada com o mesmo tamanho.

### 4.3. Fórmulas por operação e justificativas

#### 4.3.1. Busca exata na Trie — `Trie.buscar`

Primeiro se tenta percorrer a palavra. Se todo o caminho existe, verifica-se uma marca de fim, independentemente de ela ser verdadeira ou falsa:

`T_contado(m) = m + 1`

Para `dados`, são cinco caracteres e uma verificação: `T_contado(5) = 6`. Um caminho completo como `dado` pode retornar falso, mas ainda conta `4 + 1 = 5`. Se um filho necessário não existe, a execução termina durante o percurso e não verifica uma marca final:

`T_contado(r) = r`, com `1 ≤ r ≤ m`

Numa Trie que contém apenas `dados`, buscar `dez` tenta d e e, totalizando dois passos. O pior percurso cresce com m: O(m), no modelo médio de acesso aos filhos. O contador não mede a busca vazia pela interface, pois a entrada é rejeitada antes de chamar o algoritmo.

#### 4.3.2. Inserção — `Trie.inserir`

A inserção examina m caracteres, cria u nós, verifica uma marca final e, se a palavra é nova, registra um cadastro:

`T_contado(m, u, b) = m + u + 1 + b`

Em uma Trie vazia, inserir `dados` tem `m = 5`, `u = 5` e `b = 1`: `5 + 5 + 1 + 1 = 12`. Uma palavra nova pode aproveitar nós existentes: se o caminho completo já existe como prefixo de outra palavra, u é zero, mas b é um. Para uma duplicata, `u = 0` e `b = 0`, obtendo `m + 1`; repetir `dados` conta seis passos.

Como `u ≤ m` e `b ≤ 1`, o total está limitado por `2m + 2`. A inserção é O(m), embora o número observado dependa dos caminhos já cadastrados.

#### 4.3.3. Busca por prefixo na Trie — `Trie.buscar_prefixo`

Se o caminho existe, contamos p caracteres e uma verificação final do nó do prefixo. Cada descendente acrescenta uma visita e uma verificação, totalizando 2n. Recuperar k sugestões acrescenta k; montar suas strings acrescenta B; ordenar acrescenta q:

`T_prefixo = p + 2n + 1 + k + B + q`

Com apenas `dados` e `dança` cadastradas, consultar `da` teve `p = 2`, `n = 6`, `k = 2`, `B = 10` e `q = 2`: `2 + 12 + 1 + 2 + 10 + 2 = 29`. Consultar `dados` nessa mesma Trie retorna o próprio prefixo, sem copiar sua string: `5 + 0 + 1 + 1 + 0 + 0 = 7`. Se o prefixo está ausente, a fórmula é `T_contado = r`, com `r ≤ p`; não há exploração nem ordenação.

Antes de ordenar, o custo assintótico é O(p + n + R). A ordenação pode exigir O(k log k) comparações; considerando até L caracteres por comparação, acrescenta O(k log k · L). Portanto, percorrer o prefixo em O(p) não descreve o custo de entregar todas as sugestões.

#### 4.3.4. Palavra exata nos documentos — `MecanismoBusca.buscar_palavra`

Uma consulta ao índice localiza o conjunto de arquivos. Recuperar d nomes e ordená-los acrescenta as parcelas correspondentes:

`T_exata_documentos = 1 + d + q_d`

Uma palavra ausente conta uma consulta, com `d = 0` e `q_d = 0`. Na execução registrada, `dados` retornou cinco documentos e exigiu treze comparações: `1 + 5 + 13 = 19`.

O custo real médio inclui processar a chave com m caracteres, recuperar os nomes e compará-los. Para dois ou mais resultados, é O(m + d + d log d · f). O acesso Hash médio O(1) refere-se ao número de entradas, após considerar a chave; não torna toda a consulta O(1). Colisões podem piorar o acesso em casos desfavoráveis.

#### 4.3.5. Prefixo nos documentos — `MecanismoBusca.buscar_prefixo`

Primeiro a Trie recupera e ordena as palavras. Depois há uma consulta ao índice e recuperação/ordenação de documentos para cada uma das k palavras:

`T_prefixo_documentos = T_prefixo + Σᵢ (1 + dᵢ + qᵢ)`

Equivalente: `T_prefixo_documentos = T_prefixo + k + Σᵢ dᵢ + Σᵢ qᵢ`. Na execução de `comp`, o custo da Trie foi 632, houve 26 acessos ao índice, 57 associações recuperadas e 91 comparações de nomes: `632 + 26 + 57 + 91 = 806`.

Se o prefixo não existir na Trie, contam-se somente as r tentativas do caminho, sem consultas ao índice. Caso exista, o crescimento combina O(p + n + R + k log k · L) com os custos de recuperar e ordenar os arquivos de cada palavra. O processamento dessas palavras como chaves é limitado pelo volume R já considerado.

#### 4.3.6. Pré-processamento e construção das estruturas

Essas etapas possuem medições de tempo e análise assintótica, mas não possuem contadores de passos próprios na implementação atual. Não se atribuem a elas fórmulas exatas de `T_contado`. Para justificar crescimento, usamos **modelos aproximados de custo**, com coeficientes constantes positivos a, b, c e e, que representam trabalho por unidade, sem ajuste numérico nem correspondência com segundos.

Definimos **C** como o total de caracteres dos textos; **H** como os caracteres dos tokens filtrados, incluindo repetições; **A** como as associações distintas termo-documento; **D** como documentos processados; **V** como termos distintos; e **S** como a soma dos tamanhos desses termos.

| Etapa | Modelo de crescimento | Justificativa |
| --- | --- | --- |
| Pré-processamento | `T_modelo = aC + bD + e` → O(C + D) | Percorrer caracteres, produzir tokens e filtrar stopwords; D inclui o trabalho fixo por documento, inclusive os vazios. |
| Construção do índice | `T_modelo = aH + bA + cD + e` → O(H + A + D), em média | Hashing e eliminação de repetições, registro de associações e trabalho fixo por documento; exclui leitura e pré-processamento. |
| Construção da Trie | `T_modelo = aS + bV + e` → O(S), para vocabulário não vazio | Percorrer os caracteres e finalizar as palavras; como os termos são não vazios, V ≤ S. |

A lista de stopwords já está carregada nesses modelos. A descoberta/ordenação de arquivos, sua leitura e a apresentação dos resultados são etapas adicionais, fora desses custos específicos. Os modelos de Hash são médios; não são garantias para distribuições adversas de colisões.

### 4.4. Resumo das complexidades e memória

| Operação | Complexidade no modelo descrito |
| --- | --- |
| Inserção ou busca exata na Trie | O(m), com acesso médio constante aos filhos |
| Prefixo na Trie | O(p + n + R + k log k · L) |
| Pré-processamento da base | O(C + D) |
| Construção do índice | O(H + A + D), em média |
| Construção da Trie do vocabulário | O(S), para vocabulário não vazio |
| Palavra exata em documentos | O(m + d + d log d · f), em média |
| Prefixo em documentos | O(p + n + R + k log k · L + Σᵢ[dᵢ + dᵢ log dᵢ · f]), em média |

As parcelas de ordenação valem zero para listas com zero ou um elemento. Não se calcula `log(0)`. Comparar strings e processar chaves pode envolver vários caracteres, por isso L, f e m aparecem nos limites, mesmo quando o contador atribui uma unidade a uma comparação ou acesso.

Para memória, definimos **N** como o total de caracteres dos nomes dos documentos. As estruturas persistentes usam O(S + A + D + N): nós e transições da Trie, vocabulário, associações, metadados e nomes. Durante a preparação, há também o conteúdo, tokens e conjunto de termos do arquivo atual. Textos completos de todos os documentos não são mantidos simultaneamente. Durante consultas, a pilha, as sugestões e os nomes recuperados ocupam espaço adicional proporcional aos percursos e resultados. Objetos e dicionários por nó aumentam o consumo prático da Trie tradicional.

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

As medianas abaixo são o registro original, anterior à inclusão do contador de passos nos menus. O experimento usou Python 3.12.14 no Windows, com os primeiros 1, 3 e 5 arquivos em ordem alfabética. O grupo de três contém algoritmos, banco de dados e engenharia de software. Houve um aquecimento por grupo e 15 repetições; a tabela apresenta medianas em milissegundos. A leitura fica fora dos tempos de construção; a consulta inclui recuperar e ordenar resultados, excluindo impressão e entrada do usuário.

| Documentos | Tokens | Termos | Pré-processamento (ms) | Índice (ms) | Trie (ms) | Exata `dados` (ms) | Prefixo `comp` (ms) |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | 752 | 342 | 0,4543 | 0,0694 | 0,5474 | 0,0015 | 0,0273 |
| 3 | 2.312 | 727 | 1,3792 | 0,2653 | 1,3030 | 0,0019 | 0,0388 |
| 5 | 3.850 | 1.022 | 2,3482 | 0,4456 | 2,0652 | 0,0031 | 0,0570 |

Nesta execução, o pré-processamento cresceu aproximadamente com o volume de texto. A Trie acompanhou o crescimento do vocabulário e de seus caracteres. A consulta por prefixo teve custo maior que a exata, pois materializou várias palavras e suas associações. A exata também retornou mais arquivos nos grupos maiores; sua duração não mede somente o acesso Hash. São observações compatíveis com os custos descritos, sem provar as classes assintóticas. Tempos pequenos variam conforme computador, cache, alocação e outros processos; a ordem fixa dos grupos também limita a interpretação experimental.

### 5.1. Conferência entre fórmulas e passos observados

As execuções abaixo usaram o contador e o relógio simultaneamente. Os quatro primeiros exemplos usam uma Trie inicialmente vazia, na qual `dados` é inserida e depois reinserida. Para o quinto, acrescenta-se `dança`. Os dois últimos usam os cinco documentos entregues. Os tempos incluem a instrumentação e são amostras individuais; não são as medianas sem contador da tabela anterior.

| Operação | Entrada | Substituição na fórmula | Passos observados | Tempo (ms) |
| --- | --- | --- | ---: | ---: |
| Inserção em Trie vazia | `dados` | 5 + 5 + 1 + 1 = 12 | 12 | 0,0093 |
| Inserção duplicada | `dados` | 5 + 0 + 1 + 0 = 6 | 6 | 0,0019 |
| Busca exata na Trie | `dados` | 5 + 1 = 6 | 6 | 0,0033 |
| Busca com falha antecipada | `dez` | r = 2 | 2 | 0,0016 |
| Prefixo em Trie com dados e dança | `da` | 2 + 2·6 + 1 + 2 + 10 + 2 = 29 | 29 | 0,0168 |
| Busca exata nos documentos | `dados` | 1 + 5 + 13 = 19 | 19 | 0,0227 |
| Prefixo nos documentos | `comp` | 632 + 26 + 57 + 91 = 806 | 806 | 0,1281 |

No prefixo `comp`, a parcela da Trie é `4 + 2·101 + 1 + 26 + 268 + 131 = 632`. As 57 associações de documentos não são 57 arquivos distintos: o mesmo arquivo pode ser associado a várias sugestões. As comparações 131, 13 e 91 são valores desta execução e podem mudar com a enumeração inicial dos dados.

Cada total foi conferido contra a fórmula antes de gerar [contagens_passos.json](evidencias/contagens_passos.json), que preserva entradas, resultados, parâmetros, etapas contadas e tempos. As contagens demonstram o modelo de operações selecionadas; as fórmulas de O(...) explicam o crescimento e os custos que o contador não observa.

### 5.2. Evidências e reprodução

[medicoes.json](evidencias/medicoes.json) guarda todas as amostras, contagens, hashes das entradas e exemplos. [demonstracao.txt](evidencias/demonstracao.txt) guarda entradas e a saída real de uma sessão. Alterações na base exigem novas medições e atualização deste relatório.

## 6. Respostas às questões conceituais da Parte I

1. **Por que uma Trie é adequada para autocomplete?** O prefixo aponta diretamente para um caminho; somente seus descendentes precisam ser explorados para obter sugestões. Não é necessário comparar o prefixo com todas as palavras do vocabulário.
2. **Qual a vantagem sobre busca sequencial?** Uma lista sem índice pode exigir examinar todas as palavras, com custo dependente de sua quantidade e dos caracteres comparados. A Trie localiza o caminho em função do comprimento do prefixo e depois trabalha sobre o subconjunto correspondente. Ainda existe custo para devolver as sugestões.
3. **Como prefixos comuns são representados?** São compartilhados nos mesmos nós e arestas iniciais. `programa` e `programação` seguem o mesmo caminho inicial; a marca de fim permite terminar uma palavra e continuar até outra.
4. **Qual a complexidade de buscar uma palavra de tamanho m?** O(m) no modelo médio desta implementação, com acesso aos filhos por dicionário. São percorridos até m caracteres e verificada a marca de fim.
5. **Qual problema de memória pode ocorrer?** Cada caractere novo pode criar um nó com um dicionário, referências e marca de fim. Muitas palavras com pouco compartilhamento produzem muitos nós; o custo dos objetos pode superar o espaço ocupado apenas pelas strings.
6. **O que é uma Trie comprimida?** É uma variante que pode reunir trechos de caminhos sem ramificação em arestas rotuladas por sequências de caracteres. Reduz nós e referências intermediárias, mas exige comparar trechos e dividir arestas em determinadas inserções. Foi discutida conceitualmente, sem implementação neste projeto.

## 7. Validação, limitações e fonte

Os **33 testes automatizados passaram**. Eles verificam busca exata versus prefixo, duplicatas, inserções, Unicode, stopwords, contagens, integração Trie/índice, descoberta de novo arquivo na execução seguinte, arquivos vazios e ilegíveis, menus e execução a partir de outra pasta. Sete testes adicionais conferem contagens conhecidas, falhas antecipadas, duplicatas, ordenação e integração entre Trie e Hash. Uma palavra de 2.000 caracteres também confirma que a busca por prefixo não depende de recursão.

A solução não inclui busca por frases, ranking, frequências, posições, correção ortográfica, remoção de acentos, stemming, lematização nem KMP. Os índices são reconstruídos ao iniciar; arquivos adicionados durante a sessão entram apenas na próxima execução. A lista de stopwords é simples e pode remover informação relevante em alguns contextos. A ordenação segue strings Unicode, sem regras linguísticas específicas do português. A Trie tradicional e a preparação integral da base podem consumir memória significativa em coleções grandes.

**Fonte de requisitos:** enunciado local *Trabalho Prático - A1 - Unidade_2_Processamento_Textos.docx*, professor André Lucio, lido em 03/10/2026. Textos de teste, decisões, respostas e análise foram preparados para esta implementação; não constituem gabarito oficial. Código e relatório devem ser revisados pelos integrantes antes da entrega. Prazo, matrículas e exigências adicionais não foram presumidos. A conversão para PDF está reservada ao momento da entrega.
