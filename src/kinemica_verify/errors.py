"""Domain errors raised by Kinemica Verify."""


class KinemicaVerifyError(Exception):
    """Base error for invalid contracts, evidence, or verification inputs."""


class SchemaValidationError(KinemicaVerifyError):
    """Raised when structured input does not satisfy its schema."""


class SignatureVerificationError(KinemicaVerifyError):
    """Raised when a signed verification record cannot be authenticated."""
