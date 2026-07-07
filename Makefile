PY = PYTHONPATH=./pipeline ./pys
#RAW_PRICES = public/prices.json
#FIXED_PRICES = public/fixed_prices.json
PARAM=eu-de,eu-nl
PAGES_URL=http://localhost:9000/
GITHUB_OUTPUT=/dev/null

.PHONY: help fetch


help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## ' Makefile | sort | \
	  awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2}'

fetch: ## Fetch data and save to a file
	@mkdir -p deploy
	$(PY) -m pipeline \
			$$([ -f "cached.json" ] && echo --load cached.json) \
			--cksum deploy/sum.txt \
			--output deploy/prices-latest.json \
			region=$(PARAM)

vcheck:	## Check if version has changed
	@set -x ; osum=$$(wget -nv -O- $(PAGES_URL)/sum.txt || :) ; \
	if [ -n "$$osum" ] ; then  \
		osig=$$(echo "$$osum" | awk '{ print $$1 }') ; \
		nsig=$$(awk '{ print $$1 }' deploy/sum.txt) ; \
		if [ x"$$osig" = x"$$nsig" ] ; then \
		  : Data has not changed ; \
		  echo changed=false >> "$(GITHUB_OUTPUT)" ; \
		  rm -f changed ; \
			exit 0 ; \
		fi ; \
	fi ; \
	echo changed=true | tee changed >> "$(GITHUB_OUTPUT)" ; \

publish: ## Publish a new version
	@set -x ; \
	manifest=$$(wget -nv -O- "$(PAGES_URL)/manifest.json" || :) ; \
	if [ -n "$$manifest" ] ; then  \
		echo "$$manifest" | jq -r '.[].file' | (while read js ; do \
			[ -f "deploy/$$js" ] && continue ; \
			wget -nv -Odeploy/$$js "$(PAGES_URL)/$$js" ; \
		done) ; \
	fi ; \
	size="$$(stat -c %s deploy/prices-latest.json)" ; \
	hfile="prices-$$(date +%Y-%m-%d).json" ; \
	sig=$$(awk '{ print $$1; }' deploy/sum.txt) ; \
	datetime=$$(awk '{ print $$2,$$3; }' deploy/sum.txt) ; \
	ts=$$(awk '{ print $$4; }' deploy/sum.txt) ; \
	v=$$(awk '{ for(i=5;i<=NF;i++) printf "%s%s", $$i, (i<NF ? OFS : ORS) }' deploy/sum.txt) ; \
	rec="{\"datetime\":\"$$datetime\",\"timestamp\":\"$$ts\",\"cksum\":\"$$sig\",\"file\":\"$$hfile\",\"generatedBy\":\"$$v\",\"size\":$$size}" ; \
	if [ -z "$$manifest" ] ; then \
		echo "[$$rec]" > deploy/manifest.json ; \
	elif [ -n "$$(echo "$$manifest" | jq --arg fn "$$hfile" '.[] | select(.file == $$fn)')" ] ; then \
		: Replace item ; \
		echo "$$manifest" | jq --argjson new "$$rec" --arg fn "$$file" 'map(if .file == $$fn then $$new else . end)' > deploy/manifest.json ; \
	else \
		: insert to the front ; \
		echo "$$manifest" | jq --argjson item "$$rec" '[$$item] + .' > deploy/manifest.json ; \
	fi ; \
	cp -av "deploy/prices-latest.json" "deploy/$$hfile" ; \
	echo "{\"manifest\":$$(cat deploy/manifest.json)}" | \
		$(PY) j2 -f json -o deploy/index.html html/index.html - ; \
		cp html/index.css deploy/index.css

tdep: ## Test deploy on localhost
	rm -rf www
	cp -av deploy www


serve: ## Run PHP dev server
	cd www && php -S localhost:9000

