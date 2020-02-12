# Standard Library
import re

# Third Party
from click import ClickException, echo, style

INFO = {"fg": "white"}
LABEL = {"fg": "magenta", "bold": True}
SUCCESS = {"fg": "green"}
SUCCESS_LABEL = {"fg": "green", "bold": True, "underline": True}
FAIL = {"fg": "yellow"}
FAIL_LABEL = {"fg": "yellow", "bold": True, "underline": True}
ERROR = {"fg": "red"}
ERROR_LABEL = {"fg": "red", "bold": True}
WARNING = {"fg": "yellow"}
WARNING_LABEL = {"fg": "red", "bold": True}


def _base_formatter(info, label, text, callback, **kwargs):
    """Format text block, replace template strings with keyword arguments.

    Arguments:
        info {dict} -- Text format attributes
        label {dict} -- Keyword format attributes
        text {[type]} -- Text to format
        callback {function} -- Callback function

    Returns:
        {str|ClickException} -- Formatted output
    """
    if callback is None:
        callback = style
    for k, v in kwargs.items():
        kwargs[k] = style(v, **label)
    text_all = re.split(r"(\{\w+\})", text)
    text_all = [style(i, **info) for i in text_all]
    text_all = [i.format(**kwargs) for i in text_all]
    text_fmt = "".join(text_all)
    return callback(text_fmt)


def info(text, callback=echo, **kwargs):
    """Generate formatted informational text.

    Arguments:
        text {str} -- Text to format
        callback {callable} -- Callback function (default: {echo})

    Returns:
        {str} -- Informational output
    """
    return _base_formatter(
        info=INFO, label=LABEL, text=text, callback=callback, **kwargs
    )


def error(text, callback=ClickException, **kwargs):
    """Generate formatted exception.

    Arguments:
        text {str} -- Text to format
        callback {callable} -- Callback function (default: {echo})

    Raises:
        ClickException: Raised after formatting
    """
    raise _base_formatter(
        info=ERROR, label=ERROR_LABEL, text=text, callback=callback, **kwargs
    )


def success(text, callback=echo, **kwargs):
    """Generate formatted success text.

    Arguments:
        text {str} -- Text to format
        callback {callable} -- Callback function (default: {echo})

    Returns:
        {str} -- Success output
    """
    return _base_formatter(
        info=SUCCESS, label=SUCCESS_LABEL, text=text, callback=callback, **kwargs
    )


def fail(text, callback=echo, **kwargs):
    """Generate formatted failure text.

    Arguments:
        text {str} -- Text to format
        callback {callable} -- Callback function (default: {echo})

    Returns:
        {str} -- Failure output
    """
    return _base_formatter(
        info=FAIL, label=FAIL_LABEL, text=text, callback=callback, **kwargs
    )


def warning(text, callback=echo, **kwargs):
    """Generate formatted warning text.

    Arguments:
        text {str} -- Text to format
        callback {callable} -- Callback function (default: {echo})

    Returns:
        {str} -- Warning output
    """
    return _base_formatter(
        info=WARNING, label=WARNING_LABEL, text=text, callback=callback, **kwargs
    )
