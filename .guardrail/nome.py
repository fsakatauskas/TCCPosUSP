"""Imprime o nome do arquivo de saída: primeiro nome + último sobrenome + tipo do documento.

  python3 .guardrail/nome.py 00-projeto-pesquisa  ->  Felipe Sakatauskas - Projeto de Pesquisa
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from guardrail import DOCS, ler_metadata, nome_arquivo


def main():
    doc = sys.argv[1] if len(sys.argv) > 1 else "00-projeto-pesquisa"
    meta = ler_metadata(DOCS / doc)
    nome = nome_arquivo(DOCS / doc, meta or {}) if meta else None
    print(nome or doc)
    return 0 if nome else 1


if __name__ == "__main__":
    sys.exit(main())
