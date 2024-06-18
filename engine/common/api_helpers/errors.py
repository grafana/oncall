from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class OnCallError:
    code: int
    message: str
    fields: Optional[Dict[str, List[str]]] = None


SELF_HOSTED_ONLY_FEATURE_ERROR = OnCallError(
    code=1001, message="This feature is not available in Cloud versions of OnCall"
)

INVALID_SELF_HOSTED_ID = OnCallError(code=1001, message="Invalid stack or org id for self-hosted organization")

CLOUD_ONLY_FEATURE_ERROR = OnCallError(code=1002, message="This feature is not available in OSS versions of OnCall")

INSTALL_ERROR = OnCallError(code=1003, message="Install failed check /plugin/status for details")
