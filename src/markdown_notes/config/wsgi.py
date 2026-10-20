"""WSGI config for markdown_notes project."""

import os
import sys
from pathlib import Path

# Add src to sys.path so modules are resolvable in production deployment
src_dir = Path(__file__).resolve().parent.parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "markdown_notes.config.settings")

from django.core.wsgi import get_wsgi_application  # noqa: E402

application = get_wsgi_application()
