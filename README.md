# TCCPosUSP

Gerenciamento e Estruturação de APIs: Boas práticas utilizando OpenAPI, Versionamento, Governança e Segurança.
Repo: https://github.com/fsakatauskas/TCCPosUSP

**Curso:** MBA em Engenharia de Software EaD — 2º semestre 2025
**Turma:** ENGS252

## Estrutura

```
doc/<documento>/
  metadata.yaml     # título, autor, orientador, curso, csl, bib, nocite
  NN-*.md           # seções, prefixo numérico define a ordem
  referencias.bib   # bibliografia (ABNT via --citeproc)
  abnt.csl          # estilo de citação
makefile            # alvos de compilação
```

Um diretório por documento — a saída é gerada dentro dele.

## Compilar

```sh
brew install pandoc
brew install --cask mactex-no-gui   # necessário para PDF (xelatex)
make list                          # lista os documentos disponíveis
make docx DOC=00-projeto-pesquisa   # doc/00-projeto-pesquisa/00-projeto-pesquisa.docx
make pdf  DOC=00-projeto-pesquisa   # requer TeX instalado
make html DOC=00-projeto-pesquisa
```

Sem `metadata.yaml` no diretório, o `make` aborta com aviso.

## Escrever

- Novo documento: `mkdir doc/01-artigo` e crie o `metadata.yaml` dele.
- Uma seção por arquivo `.md`, prefixo numérico define a ordem.
- Citações no estilo Pandoc: `[@chave]` — a chave vem de `referencias.bib`.
- `nocite: "@*"` no metadata lista todas as referências do bib na bibliografia final, mesmo as
  ainda não citadas no texto; remova quando todas as obras estiverem efetivamente citadas.

O esqueleto acima segue o **Template Projeto de Pesquisa (251, 252)**: identificação, Introdução,
Objetivo, Metodologia ou Material e Métodos, Resultados Esperados, Cronograma de Atividades e
Referências.

Os templates originais do curso ficam na pasta acima do repositório:
`Template Projeto de Pesquisa (251, 252).docx`, `Template TCC_PT (251, 252).docx`,
`Template Resultados Preliminares_PT (251, 252).docx` e
`Template Apresentação (251, 252).pptx`.
