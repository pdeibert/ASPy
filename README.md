# TODO
![Unit test badge](https://img.shields.io/badge/Unit_tests-passed-blue?color=rgb(0,128,0))
![Coverage badge](https://img.shields.io/badge/Coverage-93%25-blue?color=rgb(35,145,0))

# ASPY

Answer Set Programming (ASP) in Python. Currently consists of a parser & grounder as well as a (very naive) solver.

Adheres to the latest [ASP-Core-2 standard](https://arxiv.org/abs/1911.04326), but does not support weak constraints as of yet.

The grounding process generally follows the procedure described in [On the Foundations of Grounding in Answer Set Programming](https://arxiv.org/abs/2108.04769).

This library serves the following purposes:
* Provide an easy-to-use parser and grounder, as well as other tools for Answer Set Programming
* Serve as a starting point for further experimental extensions to the input language using a high-level programming language (i.e., Python)

## Installation

To install, run `pip install .`. If you wish to modify the project, install the package using the extra `dev` option: `pip install .[dev]`.

Before using `ASPy` for the first time, the ANTLR parser files need to be generated using the ANTLR runtime installed on the host system. To do so, simply run `aspy init` in a terminal. If this for some reason fails, you can manually generate the parse by calling `antlr4 -Dlanguage=Python3 -visitor -no-listener ASPCore2.g4` from the `aspy/parser` directory of the installed package.

## Usage

# TODO

### Command Line Interface

The package provides a convenient `aspy` command line tool:
```
aspy [ground|solve] -f <infile> [-o <outfile]
```
If no output file is specified, the grounded program or solutions will simply be output to the console (if successful).

### Python

Programs are usually automatically build from a convenient string notation of the input language. As an example, consider an [$n$-Queens](https://en.wikipedia.org/wiki/Eight_queens_puzzle) task with $n=4$:
```python
from aspy.program import Program
from aspy.grounding import Grounder

n_queens_prog = r'''
% n
n(0). n(1). n(2). n(3).

% choose a column for each queen on a different row
1={q(X,0);q(X,1);q(X,2);q(X,3)} :- n(X).

% no column overlap
:- q(X1,Y), q(X2,Y), X1<X2.
% no diagonal overlaps
:- q(X1,Y1), q(X2,Y2), n(N), X2=X1+N, Y2=Y1+N, N>0.
:- q(X1,Y1), q(X2,Y2), n(N), X2=X1+N, Y1=Y2+N, N>0.
'''

# parse program
prog = Program.from_string(n_queens_prog)
# ground program
ground_prog = Grounder(prog).ground()
```
This should result in the following ground program (the order of statements may differ):
```python
str(ground_prog)
```
```
n(0). n(1). n(2). n(3).

1={q(0,0);q(0,1);q(0,2);q(0,3)} :- n(0).
1={q(1,0);q(1,1);q(1,2);q(1,3)} :- n(1).
1={q(2,0);q(2,1);q(2,2);q(2,3)} :- n(2).
1={q(3,0);q(3,1);q(3,2);q(3,3)} :- n(3).

:- q(0,0), q(1,0), X1<X2.
:- q(0,0), q(2,0), X1<X2.
:- q(0,0), q(3,0), X1<X2.
:- q(0,0), q(4,0), X1<X2.
...
:- q(2,3), q(3,3), X1<X2.

:- q(0,0), q(1,1), n(1), 1=0+1, 1=0+1, 1>0.
:- q(0,0), q(2,2), n(2), 2=0+2, 2=0+2, 2>0.
:- q(0,0), q(3,3), n(3), 3=0+3, 3=0+3, 3>0.
...

:- q(0,1), q(1,0), n(1), 1=0+1, 1=0+1, 1>0.
:- q(0,2), q(2,0), n(2), 2=0+2, 2=0+2, 2>0.
:- q(0,3), q(3,0), n(3), 3=0+3, 3=0+3, 3>0.
...
```

### Development

Modifications to the input language require the parser to be modified. `ASPy` uses ANTLR4 to generate a parser based on a specified grammar. The grammar (in EBNF notation) can be found under `aspy/parser/ASPCore2.g4`. To generate the parser files, either run `aspy init` if the package is already installed, or generate them manually by calling `antlr4 -Dlanguage=Python3 -visitor -no-listener ASPCore2.g4` from the directory of the grammar file.

The parse tree is then converted into an internal representation using `aspy/parser/program_builder.py`. Internally, syntactic elements (terms, literals, rules, ...) are implemented using classes which provide convenient methods and operators for handling them, allowing for easy modification and extensions. New types of terms, literals, and statements can be derived from these classes, which reside in `aspy/program`.

The grounder and all associated functionality can be found in `aspy/grounder`.

## Additional Resources

Related repositories:
* https://github.com/potassco/clingo
* https://github.com/potassco/mu-gringo