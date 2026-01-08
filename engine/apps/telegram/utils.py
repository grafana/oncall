import asyncio
import logging
import re
from typing import Any, Coroutine, List, TypeVar, Union

logger = logging.getLogger(__name__)

uuid_regex = "[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}"
TELEGRAM_VERIFICATION_CODE_REGEX = f"^{uuid_regex}_{uuid_regex}$"

T = TypeVar("T")


def is_verification_message(text: str) -> bool:
    return bool(re.match(TELEGRAM_VERIFICATION_CODE_REGEX, text))


def run_async(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async coroutine from sync context.
    Handles event loop creation for Django/Celery.

    This is a utility function to bridge async telegram bot API calls
    from synchronous Django views and Celery tasks.

    Uses nest_asyncio to handle edge cases with nested event loops.

    Args:
        coro: The coroutine to run

    Returns:
        The result of the coroutine

    Raises:
        RuntimeError: If called from within an async context that we can't handle
    """
    # Apply nest_asyncio to allow nested event loops
    # This is required for proper async/sync bridging in Django/Celery
    try:
        import nest_asyncio  # type: ignore

        # Only apply once
        if not hasattr(run_async, "_nest_applied"):
            nest_asyncio.apply()
            run_async._nest_applied = True
    except ImportError:
        logger.warning(
            "nest-asyncio not installed. "
            "This may cause issues with async/sync bridging. "
            "Install it with: pip install nest-asyncio"
        )

    # Use asyncio.run() which properly manages event loop lifecycle
    # With nest_asyncio applied, this will work even if there's a loop in the thread
    try:
        return asyncio.run(coro)
    except RuntimeError as e:
        error_str = str(e)
        # Handle "Event loop is closed" or similar errors
        if "closed" in error_str.lower() or "Event loop" in error_str:
            logger.debug(f"Event loop issue detected ({error_str}), creating fresh loop")
            # Fallback: create a completely fresh loop and run in it
            # This should only happen in edge cases
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
                return result
            finally:
                # Don't close immediately - let it be garbage collected
                # Closing too eagerly can cause "loop is closed" errors
                try:
                    # Check if there are any pending tasks
                    pending = asyncio.all_tasks(loop)
                    if pending:
                        # Wait a bit for tasks to complete naturally
                        try:
                            loop.run_until_complete(
                                asyncio.wait_for(asyncio.gather(*pending, return_exceptions=True), timeout=0.1)
                            )
                        except asyncio.TimeoutError:
                            # Tasks didn't complete in time, cancel them
                            for task in pending:
                                if not task.done():
                                    task.cancel()
                            loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                except Exception:
                    logger.exception("Error closing event loop")
                # Don't close the loop - let Python GC handle it
                # This avoids "Event loop is closed" errors
                asyncio.set_event_loop(None)
        else:
            raise


class CallbackQueryFactory:
    SEPARATOR = ":"

    @classmethod
    def encode_data(cls, *args: Union[str, int]) -> str:
        return cls.SEPARATOR.join(map(str, args))

    @classmethod
    def decode_data(cls, data: str) -> List[str]:
        return data.split(cls.SEPARATOR)
