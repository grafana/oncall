import functools
import html
import os
import random
import re
import time
from functools import reduce

import factory
import markdown2
from bs4 import BeautifulSoup
from celery.utils.log import get_task_logger
from celery.utils.time import get_exponential_backoff_interval
from django.utils.html import urlize

logger = get_task_logger(__name__)


# Faker that always returns unique values
class UniqueFaker(factory.Faker):
    @classmethod
    def _get_faker(cls, locale=None):
        return super()._get_faker(locale).unique


# Context manager for tasks that are intended to retry
# It will rerun the whole task if exception(s) exc has happened
class OkToRetry:
    def __init__(self, task, exc, num_retries=None, compute_countdown=None, allow_jitter=True):
        self.task = task
        self.num_retries = num_retries
        self.compute_countdown = compute_countdown
        self.allow_jitter = allow_jitter

        if not isinstance(exc, (list, tuple)):
            exc = [exc]
        self.exc = exc

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None and any(issubclass(exc_type, exc) for exc in self.exc):
            if self.num_retries is None or self.task.request.retries + 1 <= self.num_retries:
                countdown = self.get_countdown(exc_val)

                logger.warning(
                    f"Retrying task gracefully in {countdown} seconds due to {exc_type.__name__}. "
                    f"args: {self.task.request.args}, kwargs: {self.task.request.kwargs}"
                )
                self.rerun_task(countdown)

                return True

    def get_countdown(self, exc_val):
        if self.compute_countdown is not None:
            countdown = self.compute_countdown(exc_val)
            if self.allow_jitter is True:
                countdown = countdown + random.uniform(0, 2)
        else:
            countdown = get_exponential_backoff_interval(
                factor=self.task.retry_backoff, retries=self.task.request.retries, maximum=600, full_jitter=True
            )
        return countdown

    def rerun_task(self, countdown):
        self.task.apply_async(
            self.task.request.args,
            kwargs=self.task.request.kwargs,
            retries=self.task.request.retries + 1,
            countdown=countdown,
        )


# lru cache version with addition of timeout.
# Timeout added to not to occupy memory with too old values
def timed_lru_cache(timeout: int, maxsize: int = 128, typed: bool = False):
    def wrapper_cache(func):
        func = functools.lru_cache(maxsize=maxsize, typed=typed)(func)
        func.delta = timeout * 10**9
        func.expiration = time.monotonic_ns() + func.delta

        @functools.wraps(func)
        def wrapped_func(*args, **kwargs):
            if time.monotonic_ns() >= func.expiration:
                func.cache_clear()
                func.expiration = time.monotonic_ns() + func.delta
            return func(*args, **kwargs)

        wrapped_func.cache_info = func.cache_info
        wrapped_func.cache_clear = func.cache_clear
        return wrapped_func

    return wrapper_cache


def getenv_boolean(variable_name: str, default: bool) -> bool:
    value = os.environ.get(variable_name)
    if value is None:
        return default

    return value.lower() in ("true", "1")


def getenv_integer(variable_name: str, default: int) -> int:
    value = os.environ.get(variable_name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def batch_queryset(qs, batch_size=1000):
    qs_count = qs.count()
    for start in range(0, qs_count, batch_size):
        end = min(start + batch_size, qs_count)
        yield qs[start:end]


def is_regex_valid(regex) -> bool:
    try:
        re.compile(regex)
        return True
    except re.error:
        return False


def isoformat_with_tz_suffix(value):
    """
    Default python datetime.isoformat() return tz offset like +00:00 instead of military tz suffix (e.g.Z for UTC)".
    On the other hand DRF returns datetime with military tz suffix.
    This utility function exists to return consistent datetime string in api.
    Is is copied from DRF DateTimeField.to_representation
    """
    value = value.isoformat()
    if value.endswith("+00:00"):
        value = value[:-6] + "Z"
    return value


def is_string_with_visible_characters(string):
    return type(string) == str and not string.isspace() and not string == ""


def str_or_backup(string, backup):
    return string if is_string_with_visible_characters(string) else backup


def clean_html(text):
    text = "".join(BeautifulSoup(text, features="html.parser").find_all(string=True))
    return text


def convert_slack_md_to_html(text):
    text = re.sub(r"\*", "**", text)
    return convert_md_to_html(text)


def convert_md_to_html(text):
    # Markdown expects two or more spaces at the end of a line to indicate a line break.
    # Adding two spaces to any line break to support templates that were built without this in mind.
    # https://daringfireball.net/projects/markdown/syntax#p
    text = text.replace("\n", "  \n")

    extras = {
        "cuddled-lists",
        "code-friendly",  # Disable _ and __ for em and strong.
        # This gives us <pre> and <code> tags for ```-fenced blocks
        "fenced-code-blocks",
        "pyshell",
        "nl2br",
        "target-blank-links",
        "nofollow",
        "pymdownx.emoji",
        "pymdownx.magiclink",
        "tables",
    }
    try:
        text = markdown2.markdown(
            text,
            extras=extras,
        )
    except AssertionError:
        # markdown2 raises an AssertionError when using the "cuddled-lists" extra and passing strings with "- - " in it.
        # If the initial attempt fails, try again without the "cuddled-lists" extra.
        text = markdown2.markdown(
            text,
            extras=extras - {"cuddled-lists"},
        )

    return text.strip()


def clean_markup(text):
    html = markdown2.markdown(text, extras=["cuddled-lists", "fenced-code-blocks", "pyshell"]).strip()
    cleaned = clean_html(html)
    stroke_matches = re.findall(r"~\w+~", cleaned)
    for stroke_match in stroke_matches:
        cleaned_match = stroke_match.strip("~")
        cleaned = cleaned.replace(stroke_match, cleaned_match)
    return cleaned


def escape_html(text):
    return html.escape(text)


def urlize_with_respect_to_a(html):
    """
    Wrap links into <a> tag if not already
    """
    soup = BeautifulSoup(html, features="html.parser")
    textNodes = soup.find_all(string=True)
    for textNode in textNodes:
        if textNode.parent and getattr(textNode.parent, "name") == "a":
            continue
        urlizedText = urlize(textNode)
        textNode.replaceWith(BeautifulSoup(urlizedText, features="html.parser"))

    return str(soup)


url_re = re.compile(
    r"""(?i)\b((?:https?:(?:/{1,3}|[a-z0-9%])|[a-z0-9.\-]+[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)/)(?:[^\s()<>{}\[\]]+|\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\))+(?:\([^\s()]*?\([^\s()]+\)[^\s()]*?\)|\([^\s]+?\)|[^\s`!()\[\]{};:'".,<>?«»“”‘’])|(?:(?<!@)[a-z0-9]+(?:[.\-][a-z0-9]+)*[.](?:com|net|org|edu|gov|mil|aero|asia|biz|cat|coop|info|int|jobs|mobi|museum|name|post|pro|tel|travel|xxx|ac|ad|ae|af|ag|ai|al|am|an|ao|aq|ar|as|at|au|aw|ax|az|ba|bb|bd|be|bf|bg|bh|bi|bj|bm|bn|bo|br|bs|bt|bv|bw|by|bz|ca|cc|cd|cf|cg|ch|ci|ck|cl|cm|cn|co|cr|cs|cu|cv|cx|cy|cz|dd|de|dj|dk|dm|do|dz|ec|ee|eg|eh|er|es|et|eu|fi|fj|fk|fm|fo|fr|ga|gb|gd|ge|gf|gg|gh|gi|gl|gm|gn|gp|gq|gr|gs|gt|gu|gw|gy|hk|hm|hn|hr|ht|hu|id|ie|il|im|in|io|iq|ir|is|it|je|jm|jo|jp|ke|kg|kh|ki|km|kn|kp|kr|kw|ky|kz|la|lb|lc|li|lk|lr|ls|lt|lu|lv|ly|ma|mc|md|me|mg|mh|mk|ml|mm|mn|mo|mp|mq|mr|ms|mt|mu|mv|mw|mx|my|mz|na|nc|ne|nf|ng|ni|nl|no|np|nr|nu|nz|om|pa|pe|pf|pg|ph|pk|pl|pm|pn|pr|ps|pt|pw|py|qa|re|ro|rs|ru|rw|sa|sb|sc|sd|se|sg|sh|si|sj|Ja|sk|sl|sm|sn|so|sr|ss|st|su|sv|sx|sy|sz|tc|td|tf|tg|th|tj|tk|tl|tm|tn|to|tp|tr|tt|tv|tw|tz|ua|ug|uk|us|uy|uz|va|vc|ve|vg|vi|vn|vu|wf|ws|ye|yt|yu|za|zm|zw)\b/?(?!@)))""",  # noqa: E501
    re.IGNORECASE,
)


def trim_if_needed(text, default=150):
    if len(text) > default:
        text = text[:default]
        text += "..."
    return text


class NoDefaultProvided(object):
    pass


def getattrd(obj, name, default=NoDefaultProvided):
    """
    Same as getattr(), but allows dot notation lookup
    Discussed in:
    http://stackoverflow.com/questions/11975781
    """

    try:
        return reduce(getattr, name.split("."), obj)
    except AttributeError as e:
        if default != NoDefaultProvided:
            return default
        raise e
