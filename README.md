# TCCPosUSP

Gerenciamento e Estruturação de APIs REST com OpenAPI, Versionamento, Governança e Segurança.
Repo: https://github.com/fsakatauskas/TCCPosUSP

**Curso:** MBA em Engenharia de Software EaD - 2º semestre 2025

## Estrutura

```
doc/<documento>/
  metadata.yaml              # título, autor, orientador, curso, csl, bib, nocite
  NN-*.md                    # seções, prefixo numérico define a ordem
  referencias.bib            # bibliografia
  normas-usp-esalq.csl       # estilo de citação institucional (autor-data)
  referencia.docx            # template oficial — estilos do .docx (Arial)
  estilo.css                 # estilos do .html
output/                      # gerados aqui — Sakatauskas.pdf, .docx, .html
makefile                     # alvos de compilação
```

A saída de todos os documentos fica no `output/` da raiz do repositório, nomeada
`<PrimeiroNome><ÚltimoSobrenome> <Tipo do documento>` — por exemplo
`FelipeSakatauskas Projeto de Pesquisa.docx` — como exige o Sistema de Orientação.

## Compilar

```sh
brew install pandoc
brew install --cask mactex-no-gui   # necessário para PDF (xelatex)
make list                           # lista os documentos disponíveis
make all  DOC=00-projeto-pesquisa   # pdf + docx + html
make pdf  DOC=00-projeto-pesquisa   # só output/Sakatauskas.pdf
make docx DOC=00-projeto-pesquisa
make html DOC=00-projeto-pesquisa
make clean                          # apaga output/

make all DOC=00-projeto-pesquisa TOC=1 NUM=1   # versão final: sumário + seções numeradas
```

Sem `metadata.yaml` no diretório, o `make` aborta com aviso. O Projeto de Pesquisa **não leva
sumário nem numeração** (padrão do template institucional); ambos são obrigatórios na versão final
do TCC — para ela, use `TOC=1 NUM=1`.

Ao gerar com `NUM=1`, o `#` de título em `00-identificacao.md` também é numerado. Na versão final,
mova o título para a chave `title:` do metadata (o template do TCC tem folha de rosto) e mantenha o
`#` fora do arquivo.

## Normas institucionais

O MBA USP/ESALQ não usa ABNT; segue o *Manual de Instruções e Normas para Trabalhos de Conclusão
de Curso*. O que já está aplicado:

- **Referências** no padrão institucional, via `normas-usp-esalq.csl`: sobrenome com apenas a
  inicial maiúscula, iniciais dos prenomes, ano logo após a autoria, títulos sem negrito ou itálico
  (primeira letra maiúscula apenas na primeira palavra).
- **Tempo verbal** no futuro do indicativo nas seções de planejamento (Metodologia, Resultados
  Esperados e Cronograma).
- **Template oficial** como base do `.docx` (`referencia.docx`), com `Normal` em Arial 12 pt.

## Fonte

Arial 12 pt em todas as saídas: `mainfont=Arial` no PDF, o tema de `referencia.docx` no Word e
`estilo.css` no HTML.

## Guardrail

`.guardrail/guardrail.py` valida os fontes e as saídas contra as regras institucionais:

| Regra | Verifica |
|---|---|
| `arquivo:nome` | primeiro nome + último sobrenome + tipo do documento |
| `metadata:*` | `pagetitle`, `aluno`, `orientador`, `curso` presentes |
| `titulo:15-palavras` | título com no máximo 15 palavras |
| `titulo:termos-proibidos` | sem "Estudo de…", "Análise de…" etc. |
| `projeto:secoes` | as 5 seções obrigatórias do Projeto de Pesquisa |
| `tempo-verbal` | planejamento no futuro do indicativo |
| `norma-institucional` | nenhuma menção a ABNT |
| `yaml:aspas` | valores com `:` entre aspas (evita o `true`) |
| `bib:integro` | sem referências órfãs |
| `docx:*` | cabeçalho, ausência de sumário, referências no padrão |

```sh
make check       # fontes + saídas compiladas
make check-doc   # só os fontes (não precisa compilar)
make check-all   # todos os documentos
```

### Rodar ao fim de cada interação

`.guardrail/hook-settings.json` tem o hook de `Stop`. Copie o bloco `hooks` para
`.claude/settings.json` do projeto (a criação desse arquivo é bloqueada para o agente):

```sh
mkdir -p .claude && cat .guardrail/hook-settings.json > .claude/settings.json
```

## Escrever

- Novo documento: `mkdir doc/01-artigo` e crie o `metadata.yaml` dele.
- Uma seção por arquivo `.md`, prefixo numérico define a ordem.
- Citações no estilo Pandoc: `[@chave]` — a chave vem de `referencias.bib`.
- No YAML, **aspas** em valores com `:` (ex.: `"Orientador: Nome"`) — sem elas, o Pandoc lê a linha
  como mapa e imprime `true`.
- `nocite: "@*"` no metadata lista todas as referências do bib, mesmo as ainda não citadas no texto;
  remova quando todas estiverem efetivamente citadas.

## Entrega

O Projeto de Pesquisa vai pelo Sistema de Orientação (MBX) no arquivo editável do template oficial
(`.docx`), acompanhado do **Resultado do FDE em `.pdf`**.
