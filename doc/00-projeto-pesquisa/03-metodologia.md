# Metodologia

A pesquisa é de natureza aplicada, com abordagem qualitativa e objetivo exploratório. Quanto aos
procedimentos, adota-se o **estudo de caso único**, complementado por revisão bibliográfica. A
escolha se justifica por se tratar de um fenômeno contemporâneo, investigado em profundidade no
contexto real de desenvolvimento de uma API corporativa, sobre o qual o pesquisador não tem
controle sobre as variáveis.

Na primeira etapa é conduzida a revisão bibliográfica, com fontes obtidas em bases acadêmicas e
documentação técnica de referência: a especificação OpenAPI [@openapi2024], o estilo arquitetural
REST [-@fielding2000], o padrão OAuth 2.0 [@rfc6749] e o JWT [@rfc7519], além das diretrizes de
projeto de API da Microsoft [-@microsoft2024] e do Google [-@google2024] e da lista de riscos da
OWASP API Security Top 10 [@owasp2023]. Essa etapa fundamenta os critérios de avaliação adotados
nas etapas seguintes.

Na segunda etapa é desenvolvido o artefato: uma API REST implementada em C# sobre ASP.NET Core 9 ou
10, com persistência em PostgreSQL containerizada via Docker. O contrato é descrito em OpenAPI, a
evolução da API segue uma estratégia de versionamento definida a partir da revisão, e a segurança é
implementada com JWT e autorização por escopo. O pipeline de integração contínua, em GitHub Actions,
executa build, testes e validação do contrato a cada alteração.

Na terceira etapa realizam-se a coleta e a análise dos dados. As fontes de evidência são
documentais — o repositório de código, o histórico de commits, o contrato OpenAPI versionado e os
relatórios do pipeline — e a observação direta do pesquisador durante o desenvolvimento. As
técnicas de coleta são a análise documental e o levantamento de dados secundários. Os dados são
analisados de forma descritiva, confrontando o comportamento observado com os critérios derivados
da literatura, organizados em quatro dimensões: documentação, versionamento, governança e
segurança.

A análise concentra-se nos seguintes indicadores: percentual das rotas cobertas pelo contrato
OpenAPI; número de alterações com quebra de compatibilidade e como foram detectadas; consistência
da estratégia de versionamento ao longo da evolução; presença de controles de autenticação,
autorização e limitação de requisições; e grau de automatização das verificações no pipeline.

Cabe registrar as delimitações do estudo. Trata-se de caso único, com equipe reduzida, de modo que
os resultados não são generalizáveis estatisticamente, mas analiticamente. A avaliação é
predominantemente qualitativa e baseada em evidências documentais do próprio processo de
desenvolvimento, o que introduz a possibilidade de viés do pesquisador-participante — mitigada pelo
registro sistemático do contrato e do histórico de commits. A pesquisa não envolve seres humanos,
não utiliza dados pessoais ou confidenciais e não requer submissão ao Comitê de Ética em Pesquisa
[CEP].
