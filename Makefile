pylint:
	python3 -m pylint glustercli2 --disable C0116,C0114,C0115,W0511

docgen:
	python3 docgen.py > docs/README.adoc
