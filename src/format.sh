#!/bin/bash
isort . --profile black --skip aspy/parser/
black . --extend-exclude aspy/parser/