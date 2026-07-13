"""Import aller Transform-Module, damit die @transform-Registrierung greift.

Neue Transform-Datei anlegen -> hier importieren -> sie taucht automatisch
in beiden Adaptern (FastAPI + MCP) auf.
"""

from . import breach_transforms  # noqa: F401
from . import crtsh_transforms   # noqa: F401
from . import dns_transforms     # noqa: F401
from . import geo_transforms     # noqa: F401
from . import gravatar_transforms  # noqa: F401
from . import rdns_transforms    # noqa: F401
from . import shodan_transforms  # noqa: F401
from . import username_transforms  # noqa: F401
from . import wayback_transforms  # noqa: F401
from . import whois_transforms   # noqa: F401
