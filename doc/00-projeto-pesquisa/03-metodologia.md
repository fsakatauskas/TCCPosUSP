# Metodologia

A pesquisa será de natureza aplicada, com abordagem qualitativa e objetivo exploratório. Quanto aos
procedimentos, será adotado o **estudo de caso único**, complementado por revisão bibliográfica. A
escolha se justificará por se tratar de um fenômeno contemporâneo, a ser investigado em profundidade
no contexto real de desenvolvimento de uma API corporativa, sobre o qual o pesquisador não terá
controle sobre as variáveis.

Na primeira etapa será conduzida a revisão bibliográfica, com fontes a serem obtidas em bases
acadêmicas e documentação técnica de referência: a especificação OpenAPI [@openapi2024], o estilo
arquitetural REST proposto por Fielding [-@fielding2000], o padrão OAuth 2.0 [@rfc6749] e o JWT
[@rfc7519], além das diretrizes de projeto de API da Microsoft [-@microsoft2024] e do Google
[-@google2024] e da lista de riscos da OWASP API Security Top 10 [@owasp2023]. Essa etapa
fundamentará os critérios de avaliação que serão adotados nas etapas seguintes.

Na segunda etapa será desenvolvido o artefato: uma API REST a ser implementada em C# sobre ASP.NET
Core 9 ou 10, com persistência em banco de dados e containerização via Docker. O contrato será
descrito em OpenAPI, a evolução da API seguirá uma estratégia de versionamento a ser definida a
partir da revisão, e a segurança será implementada com JWT e autorização por escopo. O pipeline de
integração contínua, em GitHub Actions, executará build, testes e validação do contrato a cada
alteração. O código-fonte, os contratos OpenAPI versionados e o histórico de alterações ficarão
disponíveis publicamente em <https://github.com/fsakatauskas/TCCPosUSP>, que servirá como
instrumento de coleta documental desta pesquisa.

Na terceira etapa serão realizadas a coleta e a análise dos dados. As fontes de evidência serão
documentais — o repositório de código, o histórico de commits, o contrato OpenAPI versionado e os
relatórios do pipeline — e a observação direta do pesquisador durante o desenvolvimento. As
técnicas de coleta serão a análise documental e o levantamento de dados secundários. Os dados serão
analisados de forma descritiva, confrontando o comportamento observado com os critérios derivados da
literatura, organizados em quatro dimensões: documentação, versionamento, governança e segurança.

A análise concentrar-se-á nos seguintes indicadores: percentual das rotas cobertas pelo contrato
OpenAPI; número de alterações com quebra de compatibilidade e como serão detectadas; consistência da
estratégia de versionamento ao longo da evolução; presença de controles de autenticação, autorização
e limitação de requisições; e grau de automatização das verificações no pipeline.

Cabe registrar as delimitações do estudo. Tratar-se-á de caso único, com equipe reduzida, de modo
que os resultados não serão generalizáveis estatisticamente, mas analiticamente. A avaliação será
predominantemente qualitativa e baseada em evidências documentais do próprio processo de
desenvolvimento, o que introduzirá a possibilidade de viés do pesquisador-participante — a ser
mitigada pelo registro sistemático do contrato e do histórico de commits. A pesquisa não envolverá
seres humanos, não utilizará dados pessoais ou confidenciais e não requererá submissão ao Comitê de
Ética em Pesquisa [CEP].
