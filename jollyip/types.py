# Third Party
from click import ParamType


class Number(ParamType):
    """Custom click type to accept an integer or float value."""

    name = "number"

    def convert(self, value, param, ctx):
        """Validate & convert input value to a float or integer."""

        try:
            converted = float(value)
        except ValueError:
            self.fail("'{v}' is not a valid number".format(v=value), param, ctx)

        if converted.is_integer():
            converted = int(converted)

        return converted


NUMBER = Number()
