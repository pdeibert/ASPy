from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Optional,
    Self,
    Set,
    Tuple,
    Type,
)

import antlr4  # type: ignore

from aspy.parser.ASPCore2Lexer import ASPCore2Lexer
from aspy.parser.ASPCore2Parser import ASPCore2Parser

from .program_builder import ProgramBuilder

if TYPE_CHECKING:  # pragma: no cover
    from .literals import AggrPlaceholder, ChoicePlaceholder
    from .query import Query
    from .statements import (
        AggrBaseRule,
        AggrElemRule,
        ChoiceBaseRule,
        ChoiceElemRule,
        Statement,
    )


class Program:
    """Answer Set program.

    Represents an Answer Set program.

    Attributes:
        safe: Boolean indicating whether or not the underlying program is safe.
        ground: Boolean indicating whether or not the underlying program is ground.
    """

    def __init__(
        self, statements: Iterable["Statement"], query: Optional["Query"] = None
    ) -> None:
        """Initializes the program instance.

        Args:
            statements: Iterable over `Statement` instances.
            query: Optional `Query` instance. Defaults to None.
        """
        self.statements = tuple(statements)
        self.query = query

    def __eq__(self: Self, other: "Any") -> bool:
        """Compares the program to a given object.

        Args:
            other: `Any` instance to be compared to.

        Returns:
            Boolean indicating whether or not the program is considered equal to the given object.
        """  # noqa
        return (
            isinstance(other, Program)
            and set(self.statements) == set(other.statements)
            and self.query == other.query
        )

    def __str__(self: Self) -> str:
        """Returns the string representation for the program.

        Returns:
            String representing the program.
            Contains the string representations of all statements and the query
            on separate lines in order.
        """
        return "\n".join([str(statement) for statement in self.statements]) + (
            "\n" + str(self.query) if self.query is not None else ""
        )

    def reduct(self: Self, preds: Set[Tuple[str, int]]) -> "Program":
        """Computes the program reduction.

        Computes the program reduction as described in Kaminski & Schaub (2022):
        "On the Foundations of Grounding in Answer Set Programming".
        Filters out all rules that negatively depends on some of the specified
        predicates.

        Args:
            preds: Set of tuples representing predicate signatures.
                Each tuple is a pair consisting of a string and an integer indiciating
                a predicate identifier and arity.

        Return:
            `Program` instance.
        """
        return Program(
            tuple(
                statement
                for statement in self.statements
                if not any(
                    literal.pred() in preds for literal in statement.body.neg_occ()
                )
            )
        )

    def replace_arith(self: Self) -> "Program":
        """Replaces arithmetic terms appearing in the program.

        Note: arithmetic terms are not replaced in-place.
        Also, all arithmetic terms are simplified in the process.

        Returns:
            `Program` instance.
        """
        return Program(
            tuple(statement.replace_arith() for statement in self.statements),
            self.query,
        )

    def rewrite_aggregates(
        self: Self,
    ) -> Tuple[
        "Program",
        "Program",
        "Program",
        Dict[int, Tuple["AggrPlaceholder", "AggrBaseRule", List["AggrElemRule"]]],
    ]:
        """Rewrites aggregate expressions appearing in the program.

        Rewrites aggregate expression as described in Kaminski & Schaub (2022):
        "On the Foundations of Grounding in Answer Set Programming".

        Returns:
            Tuple consisting of three `Program` instances and a dictionary.
            The first `Program` instance represents the original program with
            aggregate expressions replaced by placeholder literals.
            The second `Program` instance consists of special statements representing
            the satisfiability of the replaced aggregate expressions for empty
            sets of aggregate elements.
            The third `Program` instance consists of special statements representing
            the instantiations and satisfiability of aggregate elements.
            The dictionary maps reference ids of the replaced aggregate expressions
            to tuples containing the corresponding placeholder literal, the statement
            representing the satisfiability of the replaced aggregate expressions for
            empty sets of aggregate elements and a list of statements representing
            the instantiations and satisfiability of its aggregate elements.
        """
        # TODO: get actual counter?
        aggr_counter = 0

        alpha_statements = []
        eps_statements = []
        eta_statements = []

        aggr_map = dict()

        for statement in self.statements:
            alpha_statement = statement.rewrite_aggregates(aggr_counter, aggr_map)

            for *_, eps_statement, eta_statements in aggr_map.values():
                eps_statements.append(eps_statement)
                eta_statements += eta_statements
                aggr_counter += 1

            alpha_statements.append(alpha_statement)

        return (
            Program(alpha_statements, self.query),
            Program(eps_statements),
            Program(eta_statements),
            aggr_map,
        )

    def rewrite_choices(
        self: Self,
    ) -> Tuple[
        "Program",
        "Program",
        "Program",
        Dict[int, Tuple["ChoicePlaceholder", "ChoiceBaseRule", List["ChoiceElemRule"]]],
    ]:
        """Rewrites choice expressions appearing in the program.

        Rewrites choice expression similarly to aggregate rewriting as described in
        Kaminski & Schaub (2022): "On the Foundations of Grounding in Answer Set Programming".

        Returns:
            Tuple consisting of three `Program` instances and a dictionary.
            The first `Program` instance represents the original program with
            choice expressions replaced by placeholder literals.
            The second `Program` instance consists of special statements representing
            the satisfiability of the replaced choice expressions for empty
            sets of choice elements.
            The third `Program` instance consists of special statements representing
            the instantiations and satisfiability of choice elements.
            The dictionary maps reference ids of the replaced choice expressions
            to tuples containing the corresponding placeholder literal, the statement
            representing the satisfiability of the replaced choice expressions for
            empty sets of choice elements and a list of statements representing
            the instantiations and satisfiability of its choice elements.
        """  # noqa
        # TODO: get actual counter?
        choice_counter = 0

        chi_statements = []
        eps_statements = []
        eta_statements = []

        aggr_map = dict()

        for statement in self.statements:
            chi_statement = statement.rewrite_choices(choice_counter, aggr_map)

            for *_, eps_statement, eta_statements in aggr_map.values():
                eps_statements.append(eps_statement)
                eta_statements += eta_statements
                choice_counter += 1

            chi_statements.append(chi_statement)

        return (
            Program(chi_statements, self.query),
            Program(eps_statements),
            Program(eta_statements),
            aggr_map,
        )

    @cached_property
    def safe(self: Self) -> bool:
        return all(statement.safe for statement in self.statements)  # TODO: query?

    @cached_property
    def ground(self: Self) -> bool:
        return all(statement.ground for statement in self.statements)  # TODO: query?

    @classmethod
    def from_string(
        cls: Type["Program"], prog_str: str, simplify_arithmetic: bool = True
    ) -> "Program":
        """Creates program from a raw string encoding.

        Args:
            prog_str: Raw string containing the Answer Set program.

        Returns:
            `Program` instance.
        """
        # get input stream
        input_stream = antlr4.InputStream(prog_str)  # type: ignore

        # tokenize input program
        lexer = ASPCore2Lexer(input_stream)
        stream = antlr4.CommonTokenStream(lexer)  # type: ignore
        stream.fill()

        # parse program
        parser = ASPCore2Parser(stream)
        tree = parser.program()

        # traverse parse tree using visitor
        statements, query = ProgramBuilder(simplify_arithmetic).visit(tree)

        return Program(statements, query)
