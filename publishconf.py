import os
import sys

sys.path.append(os.curdir)
from pelicanconf import *  # noqa: F401,F403

# Placeholder until the production domain is confirmed.
# Override per environment, e.g. SITEURL=https://example.org yarn build
SITEURL = os.environ.get("SITEURL", "https://vetnet.org")
RELATIVE_URLS = False
DELETE_OUTPUT_DIRECTORY = True
