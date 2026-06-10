class CRQError(Exception):
    pass


class ApiError(CRQError):
    pass


class AuthenticationError(CRQError):
    pass


class ConfigError(CRQError):
    pass


class DataValidationError(CRQError):
    pass
