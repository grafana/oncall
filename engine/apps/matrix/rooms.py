from functools import wraps
from inspect import iscoroutinefunction, signature
from typing import Any, Callable, List, Mapping


# I am pretty torn on whether this decorator is actually a good idea.
# * On the one hand, it extracts and compresses logic that would otherwise be scattered around
#     in basically every function in the client
# * On the other hand, it is pretty darn magical (not a compliment!), and relies heavily on
#     naming and calling convention:
#   - The wrapped function must be asynchronous, and must be called with `room_name` as a keyword argument,
#       or `room_name` must be the first positional argument in the function signature.
#   - The wrapped function must be a function on an object, and the object must provide an
#       asynchronous function named `_normalize_room_name` with a signature of `(room_name: str) -> str`
#
# (It also seems that the decorator clobbers type hints for Intellisense/Code Completion, though it's
# possible I just haven't configured my IDE correctly)
#
# This is one for the Oncall team to decide what style they'd prefer.
#
# (Regarding naming - `normalize_room_name` or `normalized_room_name` felt more natural,
# but I wanted to avoid confusion with the existing client method named `normalize_room_name` -
# that extra `d` would be easy to overlook!)

NAME_OF_NORMALIZATION_FUNCTION = '_normalize_room_name'

import logging
logger = logging.getLogger(__name__)


def room_name_normalizer():
    """
    Decorator that, given a function that accepts a Matrix `room_name` (id or alias) argument, normalizes the value of
    the argument to the `room_id`.
    """
    def wrapper(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            parent_object = args[0]
            try:
                normalization_function = getattr(parent_object, NAME_OF_NORMALIZATION_FUNCTION)
            except AttributeError:
                raise AttributeError('`@room_name_normalizer` can only be applied to functions on objects that '
                                     f'provide a `{NAME_OF_NORMALIZATION_FUNCTION}` method')

            # Check that the normalization_function has the signature that we expect -
            # otherwise, calling it below will result in some Funky Behaviour(tm)
            #
            # This is _basically_ a runtime unit test of the object's signature. In a language
            # with a stricter type system, we could define an abstract class
            # `CanNormalizeRoomNames`, define the method signature there, and then
            # depend on the fact that subclasses would override the method with the
            # same signature - but Python permits subclasses to define different
            # signatures.
            sig = signature(normalization_function)
            assert len(sig.parameters) == 1
            assert 'room_name' in sig.parameters
            assert sig.parameters['room_name'].annotation is str
            assert sig.return_annotation is str
            assert iscoroutinefunction(func)
            assert iscoroutinefunction(normalization_function)

            new_args, new_kwargs = await _find_and_normalize_room_name_in_parameters_passed_to_func(
                func, normalization_function, *args, **kwargs
            )
            return await func(*new_args, **new_kwargs)

        return wrapped

    return wrapper


async def _find_and_normalize_room_name_in_parameters_passed_to_func(
        func: Callable,
        normalization_func,
        *args: Any,
        **kwargs: Any) -> (List, Mapping[str, Any]):
    """
    Returns `(*args, **kwargs)`, with `room_name` appropriately normalized

    (Note that `Mapping[str, Any]` would be an incorrect annotation for **kwargs input:
    https://peps.python.org/pep-0484/#arbitrary-argument-lists-and-default-argument-values)
    """
    if 'room_name' in kwargs:
        kwargs['room_name'] = await normalization_func(kwargs['room_name'])
    else:
        # function was not called with `room_name` as a keyword argument.
        #
        # Iterate in parallel over the inputs and the signature definitions (noting that, when given
        # arguments of different lengths, `zip` will truncate to match the shorter sequence. That is -
        # here we are checking the first n signature arguments, where n is the number of positional
        # arguments passed at the call site). If we find signature parameter named 'room_name',
        # normalize the corresponding input positional argument...
        sig = signature(func)
        for idx, (positional_argument, function_parameter_name) in enumerate(zip(args, sig.parameters)):
            if function_parameter_name == 'room_name':
                args_as_list = list(args)  # Tuples do not support assignment
                args_as_list[idx] = await normalization_func(positional_argument)
                args = tuple(args_as_list)
                break
        else:
            # ...and, if not - that is, if `room_name` was neither passed as a positional argument nor
            # as a keyword argument - this means that `room_name` had a default value in the function definition
            # and that no value was passed for `room_name` at the call site.
            kwargs['room_name'] = await normalization_func(sig.parameters['room_name'].default)

    return args, kwargs
