# ETL Assembly

## MISP automated flow POC

This is the implementation of MISP automated flow. Here we also explore a new architecture for hooking sources and app on our ecosystem. We can think of this as an evolution of TruStash.

More docs to come...

## Environment setup

Assuming you already have [Pipenv](https://pipenv.pypa.io/en/latest/install/#installing-pipenv) and [pre-commit](https://pre-commit.com/) installed on your OS do:

```shell
pipenv install --dev
pre-commit install
```

This will create the virtual environment for this project and install dependencies including dev ones. Also pre commit hooks are going to be created and activated.

