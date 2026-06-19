class MissingEnvironmentError(Exception):
    """Raised when mandatory environment variables are absent.

    Carries the offending variable names (never their values) so callers can
    report them without leaking secrets.
    """

    def __init__(self, variables: list[str]) -> None:
        self.variables = variables
        super().__init__(
            f"Missing essential environment variables: {', '.join(variables)}"
        )
