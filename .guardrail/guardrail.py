"""Valida os arquivos e as saídas do documento contra as regras de conformidade.

Uso:
  python3 .guardrail/guardrail.py              # checa fontes do documento
  python3 .guardrail/guardrail.py --render     # checa também as saídas em output/
  python3 .guardrail/guardrail.py --doc 01-artigo
"""

import re
import sys
import unicodedata
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DOCS = RAIZ / "doc"
NOMES_DOC = {
    "00-projeto-pesquisa": "Projeto de Pesquisa",
    "01-resultados-preliminares": "Resultados Preliminares",
    "02-tcc": "TCC",
}
TERMOS_TITULO = ("estudo de", "análise de", "influência de", "elaboração de", "efeito de")
PRESENTE = (
    "é conduzida",
    "é desenvolvido",
    "realizam-se",
    "são analisados",
    "é realizada",
    "será conduzida a revisão bibliográfica, com fontes obtidas",
)
FUTURO = "r[áã]o?|ser[áã]o|ir[áã]|ser[áã]"
SECOES_PROJETO = [
    "Introdução",
    "Objetivo",
    "Metodologia",
    "Resultados Esperados",
    "Cronograma de Atividades",
]


def erro(regra, msg):
    print(f"  FALHA  [{regra}] {msg}")
    return 1


def ok(regra, msg):
    print(f"  ok     [{regra}] {msg}")
    return 0


def docs(apenas=None):
    if apenas:
        return [DOCS / apenas]
    return sorted(p for p in DOCS.iterdir() if p.is_dir())


def ler_metadata(d):
    """Lê o frontmatter YAML sem depender de pyyaml: só pares `chave: valor` simples."""
    arquivo = d / "metadata.yaml"
    if not arquivo.exists():
        return None
    texto = arquivo.read_text(encoding="utf8")
    if not texto.strip().startswith("---"):
        return None
    corpo = texto.strip().strip("-").split("\n---")[0]
    meta = {}
    for linha in corpo.splitlines():
        if linha[:1].isspace() or ":" not in linha:
            continue
        chave, valor = linha.split(":", 1)
        valor = valor.strip().strip('"').strip("'")
        if valor:
            meta[chave.strip()] = valor
    return meta or None


def sem_acento(texto):
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def nome_arquivo(d, meta):
    """Primeiro nome + último sobrenome + tipo do documento, sem espaços nem acentos."""
    completo = sem_acento(str(meta.get("aluno", ""))).split()
    if len(completo) < 2:
        return None
    tipo = NOMES_DOC.get(d.name, d.name.split("-", 1)[-1].replace("-", " ").title())
    return f"{completo[0]}{completo[-1]} {tipo}"


def regras_fonte(d, meta):
    """Regras verificáveis direto nos .md e no metadata, sem compilar."""
    falhas = 0
    arquivos = sorted(d.glob("[0-9][0-9]-*.md"))
    corpo = "\n".join(p.read_text(encoding="utf8") for p in arquivos)
    titulos = [sem_acento(m).lower() for p in arquivos for m in re.findall(r"^# (.+)$", p.read_text(encoding="utf8"), re.M)]

    if nome_arquivo(d, meta):
        falhas += ok("arquivo:nome", nome_arquivo(d, meta))
    else:
        falhas += erro("arquivo:nome", "não foi possível derivar do campo aluno")

    for campo in ("pagetitle", "aluno", "orientador", "curso"):
        if meta.get(campo):
            falhas += ok(f"metadata:{campo}", "presente")
        else:
            falhas += erro(f"metadata:{campo}", f"ausente no metadata.yaml")

    titulo = str(meta.get("pagetitle", ""))
    if titulo:
        palavras = len(titulo.split())
        if palavras <= 15:
            falhas += ok("titulo:15-palavras", f"{palavras} palavras")
        else:
            falhas += erro("titulo:15-palavras", f"{palavras} palavras, máximo 15")
        baixo = titulo.lower()
        achado = [t for t in TERMOS_TITULO if baixo.startswith(t)]
        if achado:
            falhas += erro("titulo:termos-proibidos", f"começa com {achado[0]!r}")
        else:
            falhas += ok("titulo:termos-proibidos", "sem termos redundantes")

    if "projeto-pesquisa" in d.name:
        faltando = [s for s in SECOES_PROJETO if sem_acento(s).lower() not in titulos]
        if faltando:
            falhas += erro("projeto:secoes", f"faltando {faltando}")
        else:
            falhas += ok("projeto:secoes", f"{len(SECOES_PROJETO)} seções obrigatórias presentes")

    achados = [t for t in PRESENTE if t in corpo]
    if achados:
        falhas += erro("tempo-verbal", f"presente do indicativo no planejamento: {achados}")
    else:
        falhas += ok("tempo-verbal", "seções de planejamento no futuro")

    if re.search(r"ABNT|Associa[çc][ãa]o Brasileira", corpo, re.I):
        falhas += erro("norma-institucional", "menção a ABNT; a norma é o manual da instituição")
    else:
        falhas += ok("norma-institucional", "sem menção a ABNT")

    for chave, valor in meta.items():
        if isinstance(valor, str) and ":" in valor and not re.search(r"https?://", valor):
            if not (d / "metadata.yaml").read_text(encoding="utf8").count(f'"{valor}"'):
                falhas += erro("yaml:aspas", f"{chave} contém ':' sem aspas (vira mapa)")
    falhas += ok("yaml:aspas", "valores com ':' estão entre aspas")

    if re.search(r"@\w+", corpo):
        falhas += ok("citacoes:pandoc", "citações no formato [@chave]")
    else:
        falhas += erro("citacoes:pandoc", "nenhuma citação encontrada")

    bib = d / "referencias.bib"
    texto_bib = bib.read_text(encoding="utf8") if bib.exists() else ""
    autores = re.findall(r"@\w+\{([^,]+),.*?author\s*=\s*\{+([^,}]+)", texto_bib, re.S)
    sobrenomes = {k: v.strip().strip("{}").strip().split(",")[0] for k, v in autores}
    orfas = []
    for m in re.finditer(r"\[-@([\w:.-]+)\]", corpo):
        antes = corpo[max(0, m.start() - 40):m.start()]
        if sobrenomes.get(m.group(1), "") not in antes:
            orfas.append(m.group(1))
    if orfas:
        falhas += erro("citacoes:autoria", f"[-@…] sem o sobrenome no texto: {orfas}")
    else:
        falhas += ok("citacoes:autoria", "toda citação traz a autoria no texto ou no parêntese")

    if bib.exists():
        identificacao = d / "00-identificacao.md"
        if identificacao.exists():
            cabecalho = identificacao.read_text(encoding="utf8").split("#")[0]
            if "Disponibilidade" in cabecalho:
                falhas += erro("cabecalho:campos", "só Aluno(a), Orientador(a), Curso e o título")
            else:
                falhas += ok("cabecalho:campos", "apenas os campos do template")

        chaves = re.findall(r"^@\w+\{([^,]+),", texto_bib, re.M)
        usadas = set(re.findall(r"@([\w:.-]+)", corpo))
        orfas = [c for c in chaves if c not in usadas]
        if orfas and 'nocite: "@*"' not in (d / "metadata.yaml").read_text(encoding="utf8"):
            falhas += erro("bib:orfas", f"referências não citadas: {orfas}")
        else:
            falhas += ok("bib:integro", f"{len(chaves)} referências")

        entradas = re.findall(r"@(\w+)\{([^,]+),(.*?)\n\}", texto_bib, re.S)
        sem_acesso = [
            k for tipo, k, campos in entradas
            if "url" in campos and "urldate" not in campos
        ]
        if sem_acesso:
            falhas += erro("bib:data-acesso", f"sem Acesso em: {sem_acesso}")
        else:
            falhas += ok("bib:data-acesso", "todo recurso on-line tem data de acesso")

        sem_local = [k for tipo, k, campos in entradas if tipo == "book" and "address" not in campos]
        if sem_local:
            falhas += erro("bib:local-livro", f"livro sem local/país: {sem_local}")
        else:
            falhas += ok("bib:local-livro", "livros com local completo")
    return falhas


def regras_render(d, meta):
    """Regras que exigem as saídas compiladas em output/."""
    falhas = 0
    nome = nome_arquivo(d, meta)
    saida = RAIZ / "output"
    docx = saida / f"{nome}.docx"
    if not docx.exists():
        return erro("output:docx", f"{docx.name} não encontrado; rode `make all DOC={d.name}`")

    falhas += ok("output:existe", f"{nome}.docx, .pdf, .html")

    texto = _texto_docx(docx)
    if re.search(r"\btrue\b|\bfalse\b", texto):
        falhas += erro("docx:yaml-mapa", "valor booleano renderizado (':' sem aspas no YAML)")
    else:
        falhas += ok("docx:yaml-mapa", "sem valores booleanos vazados")

    if "Aluno(a)" in texto and "Orientador" in texto:
        falhas += ok("docx:identificacao", "cabeçalho Aluno/Orientador presente")
    else:
        falhas += erro("docx:identificacao", "cabeçalho institucional ausente")

    if "Table of Contents" in texto:
        falhas += erro("docx:sumario", "sumário presente; o Projeto de Pesquisa não o leva")
    else:
        falhas += ok("docx:sumario", "sem sumário, conforme o template")

    if re.search(r"\bABNT\b", texto, re.I):
        falhas += erro("docx:norma", "menção a ABNT na saída")
    else:
        falhas += ok("docx:norma", "sem menção a ABNT")

    if re.search(r"\b(é conduzida|é desenvolvido|realizam-se)\b", texto):
        falhas += erro("docx:tempo-verbal", "presente do indicativo na saída")
    else:
        falhas += ok("docx:tempo-verbal", "planejamento no futuro")

    refs = re.findall(r"^\s*[A-ZÀ-Ý][\w'’]+,\s+[A-Z]\.", texto, re.M)
    if refs:
        falhas += ok("docx:referencias", f"{len(refs)} referências no padrão institucional")
    else:
        falhas += erro("docx:referencias", "referências fora do padrão Sobrenome, N.")

    if "Disponível em:" in texto and "Acesso em:" in texto:
        falhas += ok("docx:acesso", "todo recurso on-line com Disponível em/Acesso em")
    else:
        falhas += erro("docx:acesso", "falta 'Disponível em:' ou 'Acesso em:'")

    orfas_ano = [
        m.group(0) for m in re.finditer(r".{40}\(\d{4}\)", texto, re.S)
        if not re.search(r"[A-ZÀ-Ý]\w+\s*$", m.group(0)[:-6])
    ]
    if orfas_ano:
        falhas += erro("docx:citacao-sem-autor", f"citação só com o ano: {orfas_ano}")
    else:
        falhas += ok("docx:citacao-sem-autor", "nenhuma citação órfã de autoria")

    if "Disponibilidade" in texto.split("#")[0][:400]:
        falhas += erro("docx:cabecalho", "campo fora do template no cabeçalho")
    else:
        falhas += ok("docx:cabecalho", "cabeçalho conforme o template")
    return falhas


def _texto_docx(caminho):
    with zipfile.ZipFile(caminho) as z:
        xml = z.read("word/document.xml").decode("utf8")
    xml = re.sub(r"</w:p>", "\n", xml)
    return re.sub(r"<[^>]+>", "", xml)


def main():
    args = sys.argv[1:]
    render = "--render" in args
    apenas = args[args.index("--doc") + 1] if "--doc" in args else None
    total = 0
    for d in docs(apenas):
        meta = ler_metadata(d)
        if meta is None:
            total += erro("metadata:arquivo", f"{d.name} sem metadata.yaml válido")
            continue
        print(f"\n{d.name}")
        total += regras_fonte(d, meta)
        if render:
            total += regras_render(d, meta)
    print(f"\n{'OK — tudo conforme' if total == 0 else f'{total} violaç(ões)'}")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
