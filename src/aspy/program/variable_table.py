from typing import Dict, Optional, Self, Set, Union

from .symbols import SpecialChar
from .terms import AnonVariable, ArithTerm, ArithVariable, Variable


class VariableTable:
    """Variable table for statements and queries.

    Keeps track of the variables for a single statement or query.

    Attribues:
        variables: Dictionary mapping known `Variable` instances to booleans
            indicating whether or not the corresponding variable is global or not.
        anon_counter: Integer keeping track of the number of anonymous variables.
            Used to assign unique ids to anonymous variables.
        arith_counter: Integer keeping track of the number of arithmetic variables.
            Used to assign unique ids to arithmetic placeholder variables.
    """

    def __init__(
        self: Self,
        variables: Optional[Union[Dict[Variable, bool], Set[Variable]]] = None,
    ) -> None:
        """Initializes the variable table instance.

        Args:
            variables: Optional dictionary or set of `Variable` instances
                to initialize the table with.
                A dictionary maps `Variable` instances to booleans indicating
                whether or not the corresponding variable is global or not.
                For a set, all variables are considered to be local.
        """
        self.variables = dict()
        self.anon_counter = 0
        self.arith_counter = 0

        if variables is not None:
            self.update(variables)

    def __contains__(self: Self, var: str) -> bool:
        """Membership operator for variable table.

        Args:
            var: String representing the variable identifier to
                check membership for.

        Returns:
            Boolean indicating whether or not the specified variable
            is part of the variable table.
        """
        if var in self.variables:
            return True

        return False

    def __str__(self: Self) -> str:
        """Returns the string representation for the variable table.

        Returns:
            String representing the variable table, containing the variable identifiers
            of all known variables, separated by commas.
            Global variables are indicated by a '*' suffix to the variable identifier.
        """
        variables_str = ",".join(
            var.val if not is_global else f"{var.val}*"
            for (var, is_global) in self.variables.items()
        )

        return f"{{{variables_str}}}"

    def __getitem__(self: Self, var: Union[str, Variable]) -> bool:
        """Gets the stored 'is_global' value for a known variable.

        Args:
            var: `Variable` instance or string identifier of a variable.

        Raises:
            KeyError: Variable is unknown.
        """
        # 'var' is a variable
        if isinstance(var, Variable):
            try:
                return self.variables[var]
            except KeyError:
                raise KeyError(f"{str(var)} is not in variable table.")

        # 'var' is a string variable identifier
        for v, is_global in self.variables.items():
            if v.val == var:
                return is_global
        else:
            raise KeyError(f"{var} is not in variable table.")

    def __setitem__(self: Self, var: Variable, is_global: bool) -> None:
        f"""Sets the 'is_global' value for a known variable.

        Args:
            var: `Variable` instance.

        Raises:
            ValueError: Variable is unknown. {VariableTable.register} should be used instead.
        """  # noqa
        if var in self.variables:
            self.variables[var] = is_global
        else:
            raise ValueError(
                f"Variable {str(var)} is not known to variable table. Use {VariableTable.register} instead."  # noqa
            )

    def register(self: Self, var: Variable, is_global: bool = False) -> None:
        """Registers a new variable to the table.

        Args:
            var: `Variable` instance to register.
            is_global: Boolean indicating whether or not the variable is globa.

        Raises:
            ValueError: Variable is already known.
        """
        if var in self.variables:
            raise ValueError(f"Variable {str(var)} is already known to variable table.")
        # adjust counters if necessary
        if isinstance(var, AnonVariable):
            self.anon_counter = max(self.anon_counter, var.id + 1)
        elif isinstance(var, ArithVariable):
            self.arith_counter = max(self.arith_counter, var.id + 1)

        self.variables[var] = is_global

    def update(
        self: Self, variables: Union[Dict[Variable, bool], Set[Variable]]
    ) -> None:
        """Updates the variable table.

        Only updates existing variables or registers new ones.
        Does not delete any variables.

        Args:
            variables: Dictionary or set of `Variable` instances to initialize the table
                with. A dictionary maps `Variable` instances to booleans indicating
                whether or not the corresponding variable is global or not.
                For a set, all variables are considered to be local.
        """
        if isinstance(variables, Set):
            variables = {var: False for var in variables}

        self.variables.update(variables)

        # adjust counters if necessary
        for var in variables.keys():
            if isinstance(var, AnonVariable):
                self.anon_counter = max(self.anon_counter, var.id + 1)
            elif isinstance(var, ArithVariable):
                self.arith_counter = max(self.arith_counter, var.id + 1)

    def create(
        self: Self,
        symbol: str = "_",
        is_global: bool = False,
        register: bool = True,
        orig_term: Optional["ArithTerm"] = None,
    ) -> Variable:
        f"""Creates new variable and optionally registers it.

        Args:
            symbol: String representing the variable identifier.
                '_' or '{SpecialChar.TAU}' create anonymous and arithmetic variables,
                respectively. They do not need to contain any ids, but are inferred
                automatically. Defaults to '_'.
            is_global: Boolean indicating whether or not the variable is global.
                Defaults to `False`.

        Returns:
            `Variable` instance.

        Raises:
            ValueError: 'orig_term' not specified while creating an arithmetic
                placeholder variable.
        """
        # anonymous variable
        if symbol == "_":
            # get current id for anonymous variables
            id = self.anon_counter
            # increase counter
            self.anon_counter += 1

            # create new variable
            var = AnonVariable(id)
        # special 'arithmetic replacement' variable
        elif symbol == SpecialChar.TAU.value:
            if orig_term is None:
                raise ValueError(
                    "Variable table cannot create arithmetic variable without specifying 'orig_term'."  # noqa
                )

            # get current id for arithmetic variables
            id = self.arith_counter
            # increase counter
            self.arith_counter += 1

            # create new variable
            var = ArithVariable(id, orig_term)
        # variable
        else:
            # check if variable is already known
            # (to avoid duplicate variables where possible)
            for var in self.variables:
                if symbol == var.val:
                    # return existing variable
                    return var

            # create new variable
            var = Variable(symbol)

        if register:
            if var in self.variables:
                # update value
                self.variables[var] = is_global
            else:
                # register new variable
                self.register(var, is_global)

        # return newly created variable
        return var

    def vars(self: Self) -> Set["Variable"]:
        """Returns all variables in the table.

        Returns:
            (Possibly empty) set of `Variable` instances.
        """  # noqa
        return set(self.variables.keys())

    def global_vars(self: Self) -> Set["Variable"]:
        """Returns all global variables in the table.

        Returns:
            (Possibly empty) set of `Variable` instances.
        """  # noqa
        return set(var for (var, is_global) in self.variables.items() if is_global)

    def arith_vars(self: Self) -> Set["ArithVariable"]:
        """Returns all artihmetic placeholder variables in the table.

        Returns:
            (Possibly empty) set of 'ArithVariable' instances.
        """  # noqa
        return set(var for var in self.variables if isinstance(var, ArithVariable))
