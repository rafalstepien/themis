class MissingEnvironmentError(Exception):
    """
    Raised when mandatory environment variables are absent.
    """

    def __init__(self, variables: list[str]) -> None:
        self.variables = variables
        super().__init__(f"Missing essential environment variables: {', '.join(variables)}")
