from typing import TYPE_CHECKING, List, Optional, Self, Tuple, Union

import antlr4  # type: ignore

from aspy.parser.ASPCore2Parser import ASPCore2Parser
from aspy.parser.ASPCore2Visitor import ASPCore2Visitor
from aspy.program.literals import (
    AggrElement,
    AggrLiteral,
    Guard,
    LiteralCollection,
    Naf,
    Neg,
    PredLiteral,
)
from aspy.program.literals.aggregate import op2aggr
from aspy.program.literals.builtin import op2rel
from aspy.program.operators import AggrOp, ArithOp, RelOp
from aspy.program.query import Query
from aspy.program.statements import (
    Choice,
    ChoiceElement,
    ChoiceRule,
    Constraint,
    DisjunctiveRule,
    NormalRule,
    Statement,
    WeakConstraint,
    WeightAtLevel,
)
from aspy.program.terms import (
    ArithTerm,
    Functional,
    Minus,
    Number,
    String,
    SymbolicConstant,
    TermTuple,
)
from aspy.program.terms.arithmetic import op2arith
from aspy.program.variable_table import VariableTable

if TYPE_CHECKING:  # pragma: no cover
    from aspy.program.literals import BuiltinLiteral, Literal
    from aspy.program.terms import Term


class ProgramBuilder(ASPCore2Visitor):
    """Builds Answer Set program from ANTLR4 parse tree.

    Attributes:
        simplify_arithmetic:
        TODO
    """

    def __init__(self: Self, simplify_arithmetic: bool = True) -> None:
        """Initializes the program builder instance.

        Args:
            simplify_arithmetic: Boolean indicating whether or not to simplify
                arithmetic terms while building the program. Defaults to `True`.
        """
        self.simplify_arithmetic = simplify_arithmetic

    # Visit a parse tree produced by ASPCore2Parser#program.
    def visitProgram(
        self, ctx: ASPCore2Parser.ProgramContext
    ) -> Tuple[List[Statement], Optional[PredLiteral]]:
        """Visits 'program' context.

        Handles the following rule(s):

            program             :   statements? query? EOF
        """
        statements = []
        query = None

        for child in ctx.children[:-1]:
            # statements
            if isinstance(child, ASPCore2Parser.StatementsContext):
                statements += self.visitStatements(child)
            # query
            elif isinstance(child, ASPCore2Parser.QueryContext):
                query = self.visitQuery(child)

        return (statements, query)

    # Visit a parse tree produced by ASPCore2Parser#statements.
    def visitStatements(
        self, ctx: ASPCore2Parser.StatementsContext
    ) -> Tuple["Statement", ...]:
        """Visits 'statements'.

        Handles the following rule(s):
            statements          :   statement+

        Args:
            ctx: `ASPCore2Parser.StatementsContext` to be visited.

        Returns:
            Tuple of `Statement` instances.
        """
        return tuple([self.visitStatement(child) for child in ctx.children])

    # Visit a parse tree produced by ASPCore2Parser#query.
    def visitQuery(self: Self, ctx: ASPCore2Parser.QueryContext) -> Query:
        """Visits 'query'.

        Handles the following rule(s):
            query               :   classical_literal QUERY_MARK

        Args:
            ctx: `ASPCore2Parser.QueryContext` to be visited.

        Returns:
            `Query` instance.
        """
        return Query(self.visitClassical_literal(ctx.children[0]))

    # Visit a parse tree produced by ASPCore2Parser#statement.
    def visitStatement(self: Self, ctx: ASPCore2Parser.StatementContext) -> "Statement":
        """Visits 'statement'.

        Handles the following rule(s):
            statement           :   CONS body? DOT
                                |   head (CONS body?)? DOT
                                |   WCONS body? DOT SQUARE_OPEN weight_at_level SQUARE_CLOSE

        Args:
            ctx: `ASPCore2Parser.StatementContext` to be visited.

        Returns:
            `Statement` instance.
        """  # noqa
        # initialize empty variable table (for special counters)
        self.var_table = VariableTable()

        n_children = len(ctx.children)

        # first child is a token
        # CONS body? DOT (i.e., constraint)
        if isinstance(ctx.children[0], antlr4.tree.Tree.TerminalNode):
            # get token
            token = ctx.children[0].getSymbol()
            token_type = ASPCore2Parser.symbolicNames[token.type]

            # CONS body? DOT (i.e., constraint)
            if token_type == "CONS":
                # body
                if n_children > 2:
                    statement = Constraint(*self.visitBody(ctx.children[1]))
                else:
                    # TODO: empty constraint?
                    raise Exception("Empty constraints not supported yet.")
            # WCONS body? DOT SQUARE_OPEN weight_at_level SQUARE_CLOSE
            # (i.e., weak constraint)
            else:
                weight_at_level = self.visitWeight_at_level(ctx.children[-2])

                # body
                if n_children > 5:
                    statement = WeakConstraint(
                        self.visitBody(ctx.children[1]), weight_at_level
                    )
                else:
                    # TODO: empty constraint?
                    raise Exception("Empty weak constraints not supported yet.")
        # head (CONS body?)? DOT
        else:
            # TODO: what about choice rule???
            head = self.visitHead(ctx.children[0])
            body = self.visitBody(ctx.children[2]) if n_children >= 4 else tuple()

            if isinstance(head, Choice):
                statement = ChoiceRule(head, body)
            elif len(head) > 1:
                statement = DisjunctiveRule(head, body)
            else:
                statement = NormalRule(head[0], body)

        return statement

    # Visit a parse tree produced by ASPCore2Parser#head.
    def visitHead(
        self, ctx: ASPCore2Parser.HeadContext
    ) -> Union[Choice, Tuple[PredLiteral, ...]]:
        """Visits 'head'.

        Handles the following rule(s):
            head                :   disjunction
                                |   choice

        Args:
            ctx: `ASPCore2Parser.HeadContext` to be visited.

        Returns:
            `Choice` instance or tuple of `PredicateLiteral` instances.
        """
        # disjunction
        if isinstance(ctx.children[0], ASPCore2Parser.DisjunctionContext):
            return self.visitDisjunction(ctx.children[0])
        # choice
        else:
            return self.visitChoice(ctx.children[0])

    # Visit a parse tree produced by ASPCore2Parser#body.
    def visitBody(self: Self, ctx: ASPCore2Parser.BodyContext) -> Tuple["Literal", ...]:
        """Visits 'body'.

        Handles the following rule(s):
            body                :   (naf_literal | NAF? aggregate) (COMMA body)?

        Args:
            ctx: `ASPCore2Parser.BodyContext` to be visited.

        Returns:
            Tuple of `Literal` instances.
        """
        # naf_literal
        if isinstance(ctx.children[0], ASPCore2Parser.Naf_literalContext):
            literals = tuple([self.visitNaf_literal(ctx.children[0])])
        # NAF aggregate
        elif isinstance(ctx.children[0], antlr4.tree.Tree.TerminalNode):
            literals = tuple([Naf(self.visitAggregate(ctx.children[1]))])
        # aggregate
        else:
            literals = tuple([self.visitAggregate(ctx.children[0])])

        # COMMA body
        if len(ctx.children) > 2:
            # append literals
            literals += self.visitBody(ctx.children[-1])

        return tuple(literals)

    # Visit a parse tree produced by ASPCore2Parser#disjunction.
    def visitDisjunction(
        self, ctx: ASPCore2Parser.DisjunctionContext
    ) -> List[PredLiteral]:
        """Visits 'disjunction'.

        Handles the following rule(s):
            disjunction         :   classical_literal (OR disjunction)?

        Args:
            ctx: `ASPCore2Parser.DisjunctionContext` to be visited.

        Returns:
            List of `PredicateLiteral` instances.
        """
        # classical_literal
        literals = [self.visitClassical_literal(ctx.children[0])]

        # OR disjunction
        if len(ctx.children) > 1:
            # append literals
            literals += self.visitDisjunction(ctx.children[2])

        return literals

    # Visit a parse tree produced by ASPCore2Parser#choice.
    def visitChoice(self: Self, ctx: ASPCore2Parser.ChoiceContext) -> Choice:
        """Visits 'choice'.

        Handles the following rule(s):
            choice              :   (term relop)? CURLY_OPEN choice_elements? CURLY_CLOSE (relop term)?

        Args:
            ctx: `ASPCore2Parser.ChoiceContext` to be visited.

        Returns:
            `Choice` instance.
        """  # noqa
        moving_index = 0
        lguard, rguard = None, None

        # term relop
        if isinstance(ctx.children[0], ASPCore2Parser.TermContext):
            lguard = Guard(
                self.visitRelop(ctx.children[1]),
                self.visitTerm(ctx.children[0]),
                False,
            )
            moving_index += 3  # should now point to 'choice_elements' of 'CURLY_CLOSE'
        else:
            moving_index += 1

        # CURLY_OPEN CURLY_CLOSE
        if isinstance(ctx.children[moving_index], antlr4.tree.Tree.TerminalNode):
            elements = tuple()
            moving_index += 1  # should now point to 'relop' or be out of bounds
        # CURLY_OPEN choice_elements CURLY_CLOSE
        else:
            elements = self.visitChoice_elements(ctx.children[moving_index])
            moving_index += 2  # skip CURLY_OPEN as well; should now point to 'relop' or be out of bounds # noqa

        # relop term
        if moving_index < len(ctx.children) - 1:
            rguard = Guard(
                self.visitRelop(ctx.children[moving_index]),
                self.visitTerm(ctx.children[moving_index + 1]),
                True,
            )

        return Choice(elements, (lguard, rguard))

    # Visit a parse tree produced by ASPCore2Parser#choice_elements.
    def visitChoice_elements(
        self, ctx: ASPCore2Parser.Choice_elementsContext
    ) -> Tuple[ChoiceElement, ...]:
        """Visits 'choice_elements'.

        Handles the following rule(s):
            choice_elements     :   choice_element (SEMICOLON choice_elements)?

        Args:
            ctx: `ASPCore2Parser.Choice_elementsContext` to be visited.

        Returns:
            Tuple of `ChoiceElement` instances.
        """
        # choice_element
        elements = tuple([self.visitChoice_element(ctx.children[0])])

        # SEMICOLON choice_elements
        if len(ctx.children) > 1:
            # append literals
            elements += self.visitChoice_elements(ctx.children[2])

        return elements

    # Visit a parse tree produced by ASPCore2Parser#choice_element.
    def visitChoice_element(
        self, ctx: ASPCore2Parser.Choice_elementContext
    ) -> ChoiceElement:
        """Visits 'choice_element'.

        Handles the following rule(s):
            choice_element      :   classical_literal (COLON naf_literals?)?

        Args:
            ctx: `ASPCore2Parser.Choice_elementContext` to be visited.

        Returns:
            `ChoiceElement` instance.
        """
        # classical_literal
        atom = self.visitClassical_literal(ctx.children[0])

        # COLON naf_literals
        if len(ctx.children) > 2:
            literals = self.visitNaf_literals(ctx.children[2])
        # COLON?
        else:
            literals = tuple()

        return ChoiceElement(atom, literals)

    # Visit a parse tree produced by ASPCore2Parser#aggregate.
    def visitAggregate(
        self: Self, ctx: ASPCore2Parser.AggregateContext
    ) -> "AggrLiteral":
        """Visits 'aggregate'.

        Handles the following rule(s):
            aggregate           :   (term relop)? aggregate_function CURLY_OPEN aggregate_elements? CURLY_CLOSE (relop term)?

        Args:
            ctx: `ASPCore2Parser.AggregateContext` to be visited.

        Returns:
            `AggrLiteral` instance.
        """  # noqa
        moving_index = 0
        lguard, rguard = None, None

        # term relop
        if isinstance(ctx.children[0], ASPCore2Parser.TermContext):
            lguard = Guard(
                self.visitRelop(ctx.children[1]), self.visitTerm(ctx.children[0]), False
            )
            moving_index += 2  # should now point to 'aggregate_function'

        # aggregate_function
        func = op2aggr[self.visitAggregate_function(ctx.children[moving_index])]()
        moving_index += 2  # skip CURLY_OPEN as well; should now point to 'aggregate_elements' or 'CURLY_CLOSE' # noqa

        # CURLY_OPEN CURLY_CLOSE
        if isinstance(ctx.children[moving_index], antlr4.tree.Tree.TerminalNode):
            elements = tuple()
            moving_index += 1  # should now point to 'relop' or be out of bounds
        # CURLY_OPEN choice_elements CURLY_CLOSE
        else:
            elements = self.visitAggregate_elements(ctx.children[moving_index])
            moving_index += 2  # skip CURLY_OPEN as well; should now point to 'relop' or be out of bounds # noqa

        # relop term
        if moving_index < len(ctx.children) - 1:
            rguard = Guard(
                self.visitRelop(ctx.children[moving_index]),
                self.visitTerm(ctx.children[moving_index + 1]),
                True,
            )

        return AggrLiteral(func, elements, (lguard, rguard))

    # Visit a parse tree produced by ASPCore2Parser#aggregate_elements.
    def visitAggregate_elements(
        self, ctx: ASPCore2Parser.Aggregate_elementsContext
    ) -> Tuple[AggrElement, ...]:
        """Visits 'aggregate_elements'.

        Handles the following rule(s):
            aggregate_elements  :   aggregate_element (SEMICOLON aggregate_elements)?

        Args:
            ctx: `ASPCore2Parser.Aggregate_elementsContext` to be visited.

        Returns:
            Tuple of `AggrElement` instances.
        """
        # aggregate_element
        element = self.visitAggregate_element(ctx.children[0])
        elements = tuple([element]) if element is not None else tuple()

        # SEMICOLON aggregate_elements
        if len(ctx.children) > 1:
            # append literals
            elements += self.visitAggregate_elements(ctx.children[2])

        return elements

    # Visit a parse tree produced by ASPCore2Parser#aggregate_element.
    def visitAggregate_element(
        self, ctx: ASPCore2Parser.Aggregate_elementContext
    ) -> AggrElement:
        """Visits 'aggregate_element'.

        Handles the following rule(s):
            aggregate_element   :   terms COLON?
                                |   COLON? naf_literals?
                                |   terms COLON naf_literals

        Args:
            ctx: `ASPCore2Parser.Aggregate_elementContext` to be visited.

        Returns:
            `AggrElement` instance.
        """

        # terms
        terms = (
            self.visitTerms(ctx.children[0])
            if isinstance(ctx.children[0], ASPCore2Parser.TermsContext)
            else tuple()
        )

        # literals
        literals = (
            self.visitNaf_literals(ctx.children[-1])
            if isinstance(ctx.children[-1], ASPCore2Parser.Naf_literalsContext)
            else tuple()
        )

        if not terms and not literals:
            return None
        else:
            return AggrElement(TermTuple(*terms), LiteralCollection(*literals))

    # Visit a parse tree produced by ASPCore2Parser#aggregate_function.
    def visitAggregate_function(
        self, ctx: ASPCore2Parser.Aggregate_functionContext
    ) -> AggrOp:
        """Visits 'aggregate_function'.

        Handles the following rule(s):
            aggregate_function  :   COUNT
                                |   MAX
                                |   MIN
                                |   SUM

        Args:
            ctx: `ASPCore2Parser.Aggregate_functionContext` to be visited.

        Returns:
            `AggrOp` instance.
        """
        # get token
        token = ctx.children[0].getSymbol()

        return AggrOp(token.text)

    # Visit a parse tree produced by ASPCore2Parser#weight_at_level.
    def visitWeight_at_level(
        self, ctx: ASPCore2Parser.Weight_at_levelContext
    ) -> Tuple["Term", "Term", Tuple["Term", ...]]:
        """Visits 'weight_at_level'.

        Handles the following rule(s):
            weight_at_level     :   term (AT term)? (COMMA terms)?

        Args:
            ctx: `ASPCoreParser.Weight_at_levelContext` to be visited.

        Returns:
            Tuple consisting of two `Term` instances as well as a tuple of `Term` instances.
            The first `Term` instance represents the weight, the second one the level.
            The tuple of `Terms` represents the additional terms for uniqueness purposes.
        """  # noqa
        # weight
        weight = self.visitTerm(ctx.children[0])

        if len(ctx.children) > 0:
            # get next token
            token = ctx.children[1].getSymbol()
            token_type = ASPCore2Parser.symbolicNames[token.type]

            moving_index = 2

            # AT term
            if token_type == "AT":
                level = self.visitTerm(ctx.children[moving_index])
                moving_index += 2
            else:
                level = Number(0)

            # COMMA terms
            if moving_index < len(ctx.children):
                terms = self.visitTerms(ctx.children[moving_index])
            else:
                terms = tuple()
        else:
            level = Number(0)
            terms = tuple()

        return WeightAtLevel(weight, level, terms)

    # Visit a parse tree produced by ASPCore2Parser#naf_literals.
    def visitNaf_literals(
        self, ctx: ASPCore2Parser.Naf_literalsContext
    ) -> Tuple["Literal", ...]:
        """Visits 'naf_literals'.

        Handles the following rule(s):
            naf_literals        :   naf_literal (COMMA naf_literals)?

        Args:
            ctx: `ASPCore2Parser.Naf_literalsContext` to be visited.

        Returns:
            Tuple of `Literal` instances.
        """
        # naf_literal
        literals = tuple([self.visitNaf_literal(ctx.children[0])])

        # COMMA naf_literals
        if len(ctx.children) > 1:
            # append literals
            literals += self.visitNaf_literals(ctx.children[2])

        return literals

    # Visit a parse tree produced by ASPCore2Parser#naf_literal.
    def visitNaf_literal(
        self: Self, ctx: ASPCore2Parser.Naf_literalContext
    ) -> "Literal":
        """Visits 'naf_literal'.

        Handles the following rule(s):

            naf_literal         :   NAF? classical_literal
                                |   builtin_atom ;
        """
        # builtin_atom
        if isinstance(ctx.children[0], ASPCore2Parser.Builtin_atomContext):
            return self.visitBuiltin_atom(ctx.children[0])
        # NAF? classical_literal
        else:
            literal = self.visitClassical_literal(ctx.children[-1])

            # NAF classical_literal
            if len(ctx.children) > 1:
                # set NaF to true
                literal = Naf(literal)

            return literal

    # Visit a parse tree produced by ASPCore2Parser#classical_literal.
    def visitClassical_literal(
        self, ctx: ASPCore2Parser.Classical_literalContext
    ) -> PredLiteral:
        """Visits 'classical_literal'.

        Handles the following rule(s):
            classical_literal   :   MINUS? ID (PAREN_OPEN terms? PAREN_CLOSE)?

        Args:
            ctx: `ASPCore2Parser.Classical_literalContext` to be visited.

        Returns:
            `PredLiteral` instance.
        """
        n_children = len(ctx.children)

        # get first token
        token = ctx.children[0].getSymbol()
        token_type = ASPCore2Parser.symbolicNames[token.type]

        # MINUS ID (true) or ID (false)
        minus = True if (token_type == "MINUS") else False

        # PAREN_OPEN terms PAREN_CLOSE
        if n_children - (minus + 1) > 2:
            # parse terms
            terms = self.visitTerms(ctx.children[minus + 2])
        else:
            # initialize empty term tuple
            terms = tuple()

        return Neg(PredLiteral(ctx.children[minus].getSymbol().text, *terms), minus)

    # Visit a parse tree produced by ASPCore2Parser#builtin_atom.
    def visitBuiltin_atom(
        self, ctx: ASPCore2Parser.Builtin_atomContext
    ) -> "BuiltinLiteral":
        """Visits 'builtin_atom'.

        Handles the following rule(s):
            builtin_atom        :   term relop term

        Args:
            ctx: `ASPCore2Parser.Builtin_atomContext` to be visited.

        Returns:
            `BuiltinLiteral` instance.
        """
        comp_op = self.visitRelop(ctx.children[1])

        return op2rel[comp_op](
            self.visitTerm(ctx.children[0]), self.visitTerm(ctx.children[2])
        )

    # Visit a parse tree produced by ASPCore2Parser#relop.
    def visitRelop(self: Self, ctx: ASPCore2Parser.RelopContext) -> RelOp:
        """Visits 'relop'.

        Handles the following rule(s):
            relop               :   EQUAL
                                |   UNEQUAL
                                |   LESS
                                |   GREATER
                                |   LESS_OR_EQ
                                |   GREATER_OR_EQ

        Args:
            ctx: `ASPCore2Parser.RelOpContext` to be visited.

        Returns:
            `RelOp` instance.
        """
        # get token
        token = ctx.children[0].getSymbol()

        return RelOp(token.text)

    # Visit a parse tree produced by ASPCore2Parser#terms.
    def visitTerms(self: Self, ctx: ASPCore2Parser.TermsContext) -> Tuple["Term", ...]:
        """Visits 'terms'.

        Handles the following rule(s):
            terms               :   term (COMMA terms)?

        Args:
            ctx: `ASPCore2Parser.TermsContext` to be visited.

        Returns:
            Tuple of `Term` instances.
        """
        # term
        terms = tuple([self.visitTerm(ctx.children[0])])

        # COMMA terms
        if len(ctx.children) > 1:
            # append terms
            terms += self.visitTerms(ctx.children[2])

        return terms

    # Visit a parse tree produced by ASPCore2Parser#term.
    def visitTerm(self: Self, ctx: ASPCore2Parser.TermContext) -> "Term":
        """Visits 'term'.

        Handles the following rule(s):
            term                :   term_sum

        Args:
            ctx: `ASPCore2Parser.TermContext` to be visited.

        Returns:
            `Term` instance.
        """
        # term_sum
        term = self.visitTerm_sum(ctx.children[0])

        if isinstance(term, ArithTerm) and self.simplify_arithmetic:
            # simplify arithmetic term
            term = term.simplify()

        return term

    # Visit a parse tree produced by ASPCore2Parser#term_sum.
    def visitTerm_sum(self: Self, ctx: ASPCore2Parser.Term_sumContext) -> "Term":
        """Visits 'term_sum'.

        Handles the following rule(s):
            term_sum            :   term_sum PLUS term_prod
                                |   term_sum MINUS term_prod
                                |   term_prod

        Args:
            ctx: `ASPCore2Parser.Term_sumContext` to be visited.

        Returns:
            `Term` instance.
        """
        # term_sum (PLUS | MINUS) term_prod
        if len(ctx.children) > 1:
            # get operator token
            token = ctx.children[1].getSymbol()

            loperand = self.visitTerm_sum(ctx.children[0])
            roperand = self.visitTerm_prod(ctx.children[2])

            # PLUS | MINUS
            return op2arith[ArithOp(token.text)](loperand, roperand)
        # term_prod
        else:
            return self.visitTerm_prod(ctx.children[0])

    # Visit a parse tree produced by ASPCore2Parser#term_prod.
    def visitTerm_prod(self: Self, ctx: ASPCore2Parser.Term_prodContext) -> "Term":
        """Visits 'term_prod'.

        Handles the following rule(s):
            term_prod           :   term_prod TIMES term_atom
                                |   term_prod TIMES term_atom
                                |   term_atom

        Args:
            ctx: `ASPCore2Parser.Term_prodContext` to be visited.

        Returns:
            `Term` instance.
        """
        # term_prod (TIMES | DIV) term_atom
        if len(ctx.children) > 1:
            # get operator token
            token = ctx.children[1].getSymbol()

            loperand = self.visitTerm_prod(ctx.children[0])
            roperand = self.visitTerm_atom(ctx.children[2])

            # TIMES | DIV
            return op2arith[ArithOp(token.text)](loperand, roperand)
        # term_atom
        else:
            return self.visitTerm_atom(ctx.children[0])

    # Visit a parse tree produced by ASPCore2Parser#Term_atom.
    def visitTerm_atom(self: Self, ctx: ASPCore2Parser.Term_atomContext) -> "Term":
        """Visits 'term_atom'.

        Handles the following rule(s):
            term_atom           :   NUMBER
                                |   STRING
                                |   VARIABLE
                                |   ANONYMOUS_VARIABLE
                                |   PAREN_OPEN term PAREN_CLOSE
                                |   MINUS term_sum
                                |   symbolic_term

        Args:
            ctx: `ASPCore2Parser.Term_atomContext` to be visited.

        Returns:
            `Term` instance.
        """
        # first child is a token
        if isinstance(ctx.children[0], antlr4.tree.Tree.TerminalNode):
            # get token
            token = ctx.children[0].getSymbol()
            token_type = ASPCore2Parser.symbolicNames[token.type]

            # NUMBER
            if token_type == "NUMBER":
                return Number(int(token.text))
            # STRING
            elif token_type == "STRING":
                return String(token.text[1:-1])
            # VARIABLE
            elif token_type == "VARIABLE":
                return self.var_table.create(token.text, register=False)
            # ANONYMOUS_VARIABLE
            elif token_type == "ANONYMOUS_VARIABLE":
                return self.var_table.create(register=False)
            # PAREN_OPEN term PAREN_CLOSE
            elif token_type == "PAREN_OPEN":
                # TODO: is (term) really identical to term?
                return self.visitTerm(ctx.children[1])  # parse term
            # MINUS arith_atom
            elif token_type == "MINUS":
                term = self.visitTerm_sum(ctx.children[1])

                if not isinstance(term, (Number, ArithTerm)):
                    raise ValueError(
                        f"Invalid argument of type {type(term)} for arithmetic operation 'MINUS'."
                    )
                return Minus(term)
            else:
                # TODO
                raise Exception()
        # symbolic_term
        else:
            return self.visitSymbolic_term(ctx.children[0])

    # Visit a parse tree produced by ASPCore2Parser#Symbolic_term.
    def visitSymbolic_term(
        self: Self, ctx: ASPCore2Parser.Symbolic_termContext
    ) -> Union[SymbolicConstant, Functional]:
        """Visits 'symbolic_term'.

        Handles the following rule(s):
            symbolic_term       :   ID (PAREN_OPEN terms? PAREN_CLOSE)?

        Args:
            ctx: `ASPCore2Parser.Symbolic_termContext` to be visited.

        Returns:
            `Term` instance.
        """
        symbolic_id = ctx.children[0].getSymbol().text

        # ID
        if len(ctx.children) == 1:
            # return symbolic constant
            return SymbolicConstant(symbolic_id)
        # ID PAREN_OPEN terms? PAREN_CLOSE
        else:
            if not isinstance(ctx.children[-2], antlr4.tree.Tree.TerminalNode):
                terms = self.visitTerms(ctx.children[-2])
            else:
                terms = tuple()

            # return functional term
            return Functional(symbolic_id, *terms)
