from rest_framework import status
from rest_framework.exceptions import (
    APIException,
    AuthenticationFailed,
    NotAuthenticated,
    PermissionDenied,
    ValidationError,
    NotFound,
    Throttled,
)
from rest_framework.response import Response
from rest_framework.views import exception_handler


ERROR_CODE_MAP = {
    AuthenticationFailed: 'authentication_failed',
    NotAuthenticated: 'not_authenticated',
    PermissionDenied: 'permission_denied',
    NotFound: 'not_found',
    ValidationError: 'validation_error',
    Throttled: 'throttled',
}


def _get_error_code(exc):
    for exc_type, code in ERROR_CODE_MAP.items():
        if isinstance(exc, exc_type):
            return code
    if isinstance(exc, APIException):
        return getattr(exc, 'default_code', 'api_error')
    return 'server_error'


def _get_message(exc, response):
    if isinstance(exc, ValidationError):
        return 'Ошибка валидации.'
    if isinstance(exc, (AuthenticationFailed, NotAuthenticated)):
        return 'Требуется авторизация.'
    if isinstance(exc, PermissionDenied):
        return 'Доступ запрещён.'
    if isinstance(exc, NotFound):
        return 'Ресурс не найден.'
    if isinstance(exc, Throttled):
        return 'Слишком много запросов.'
    if response is not None and isinstance(exc, APIException):
        detail = getattr(exc, 'detail', None)
        if isinstance(detail, str):
            return detail
    return 'Внутренняя ошибка сервера.'


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return Response(
            {
                'error': {
                    'code': 'server_error',
                'message': 'Внутренняя ошибка сервера.',
                    'details': None,
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    code = _get_error_code(exc)
    message = _get_message(exc, response)
    details = response.data

    response.data = {
        'error': {
            'code': code,
            'message': message,
            'details': details,
        }
    }
    return response
