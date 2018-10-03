class JvPlotError(Exception):

    def __init__(self, msg):
        super().__init__()
        self.msg = msg

    def __str__(self):
        return self.msg


class WrongUsage(JvPlotError):

    pass


class InvalidParameterName(WrongUsage):

    pass
