# Coding Standards

## Python
- Use `|` instead of `Union` and `Optional`
- For the lightweight data structures that do not require validation, use `dataclasses` library. For the data structures that require validation use `pydantic`. 
- Use `logging` module to provide descriptive execution logs for easy debugging.

## Testing
- Use Given-When-Then pattern

## Architecture
- Raise Low, Catch High: Deep low-level components (such as a database query executor or a HTTP network fetcher) must not handle execution errors by fallback defaults or printing messages. They must raise descriptive, domain-specific exceptions up the execution stack. Catching and logging exceptions should be deferred to the edges of the application layer (such as API routers, background workers, or CLI interfaces)
- Preserve Traceback Context: When translating a lower-level exception into a domain-specific error, chain exceptions using the `from` keyword.
- domain layer contains business logic
- controllers only orchestrate
- Follow the principles of Hexagonal App design (Ports and Adapters):
    - Define domain models, business rules and use cases in the core "domain" layer
    - Define ports (interfaces) that explain how to interact with core. Driving (inbound) ports that allow the outside world to call into the core. Driven (outbound) ports that the core uses to talk to the outside world.
    - Adapters (implementation) that wrap around the ports to handle technology-specific details
- Use dependency injection


## Docker
- Use multi-stage builds to keep the images lean. For builder stage copy only the dependency definitions and lock them in a frozen state, ensuring that compilation occurs entirely in isolation before copying the virtual environment over to a clean, minimal runtime image.
