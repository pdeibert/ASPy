#!/bin/bash
isort . --check-only --profile black --skip aspy/parser/
black . --check --extend-exclude aspy/parser/