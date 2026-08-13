class AIServiceError(Exception):
    pass


class ConversationNotFoundError(Exception):
    pass


class UserAlreadyExistsError(Exception):
    pass


class InvalidCredentialsError(Exception):
    pass


class UserNotRegisteredError(Exception):
    pass
