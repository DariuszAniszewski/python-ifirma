class PythonIfirmaExceptionFactory:
    @staticmethod
    def throw_exception_by_code(code):
        if code == 201:
            raise BadRequestParameters()
        elif code == 400:
            raise BadRequestStructureException()
        raise UnknownException()


class PythonIfirmaException(BaseException):
    code = None


class UnknownException(PythonIfirmaException):
    code = -1


class BadRequestParameters(PythonIfirmaException):
    code = 201


class BadRequestStructureException(PythonIfirmaException):
    code = 400

