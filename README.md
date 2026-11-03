# TCCPosUSP

Gerenciamento e Estruturação de APIs: Boas práticas utilizando OpenAPI, Versionamento, Governança e Segurança.
Repo: https://github.com/fsakatauskas/TCCPosUSP

**Curso:** MBA em Engenharia de Software EaD - 2º semestre 2025

## Estrutura

```
doc/<documento>/
  metadata.yaml     # título, autor, orientador, curso, csl, bib, nocite
  NN-*.md           # seções, prefixo numérico define a ordem
  referencias.bib   # bibliografia (ABNT via --citeproc)
  abnt.csl          # estilo de citação
  referencia.docx   # estilos do .docx (fonte Arial)
  estilo.css        # estilos do .html
output/             # gerados aqui — <documento>.pdf, .docx, .html
makefile            # alvos de compilação
```

A saída de todos os documentos fica no `output/` da raiz do repositório.

## Fonte

Todo o documento usa **Arial 12 pt**: `mainfont=Arial` no PDF, o tema de
`referencia.docx` no Word e `estilo.css` no HTML.

Para trocar de fonte: edite `mainfont=` no makefile, o `<a:majorFont>`/`<a:minorFont>` de
`referencia.docx` (é um zip — `word/theme/theme1.xml`) e a `font-family` do `estilo.css`.

## Compilar

```sh
brew install pandoc
brew install --cask mactex-no-gui   # necessário para PDF (xelatex)
make list                           # lista os documentos disponíveis
make all  DOC=00-projeto-pesquisa   # pdf + docx + html
make pdf  DOC=00-projeto-pesquisa   # só output/00-projeto-pesquisa.pdf
make docx DOC=00-projeto-pesquisa
make html DOC=00-projeto-pesquisa
make clean                          # apaga output/
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
