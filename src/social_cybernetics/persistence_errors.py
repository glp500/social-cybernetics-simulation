"""Shared errors for fail-closed scientific output boundaries."""


class BundlePublicationError(RuntimeError):
    """Base error for a bundle that could not be safely published."""


class BundleExistsError(BundlePublicationError):
    """Raised when publication would replace an existing filesystem entry."""


class AtomicPublicationUnavailableError(BundlePublicationError):
    """Raised when the platform cannot provide atomic no-overwrite publication."""


class BundleValidationError(BundlePublicationError):
    """Raised when a staged or published bundle violates its persistent contract."""
