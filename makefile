# make pdf DOC=00-proposta | make list | make clean
DOC    ?= 00-projeto-pesquisa
DIR    := doc/$(DOC)
META   := $(DIR)/metadata.yaml
SRC    := $(sort $(wildcard $(DIR)/*.md))
SHARED := --metadata-file=$(META) --citeproc --toc --number-sections --resource-path=.:$(DIR)

pdf: check
	pandoc $(SHARED) $(SRC) -o $(DIR)/$(DOC).pdf --pdf-engine=xelatex -V geometry:margin=3cm -V fontsize=12pt

docx: check
	pandoc $(SHARED) $(SRC) -o $(DIR)/$(DOC).docx

html: check
	pandoc $(SHARED) $(SRC) -o $(DIR)/$(DOC).html --standalone --embed-resources

list:
	@ls -d doc/*/ | sed 's|doc/||;s|/||'

check:
	@test -f "$(META)" || { echo "sem $(META)"; exit 1; }

clean:
	rm -f doc/*/*.pdf doc/*/*.docx doc/*/*.html

.PHONY: pdf docx html list check clean
