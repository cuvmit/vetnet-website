AUTHOR = "VETNET"
SITENAME = "VETNET"
SITESUBTITLE = "Open data for veterinary AI"
SITEURL = ""

TIMEZONE = "UTC"
DEFAULT_LANG = "en"

PATH = "content"
PAGE_PATHS = ["pages"]
ARTICLE_PATHS = ["news"]
STATIC_PATHS = ["images", "extra"]
EXTRA_PATH_METADATA = {
    "extra/robots.txt": {"path": "robots.txt"},
    "extra/favicon.svg": {"path": "favicon.svg"},
}
THEME = "themes/vetnet"
IGNORE_FILES = [".#*", ".gitkeep"]

# Directory-style URLs: S3/CloudFront serve index.html per directory.
PAGE_URL = "{slug}/"
PAGE_SAVE_AS = "{slug}/index.html"
ARTICLE_URL = "news/{slug}/"
ARTICLE_SAVE_AS = "news/{slug}/index.html"

# The article index lives at /news/ (the home page owns /index.html).
# Other generated listing pages are not used.
INDEX_SAVE_AS = "news/index.html"
INDEX_URL = "news/"
ARTICLE_ORDER_BY = "reversed-date"
ARCHIVES_SAVE_AS = ""
AUTHORS_SAVE_AS = ""
CATEGORIES_SAVE_AS = ""
TAGS_SAVE_AS = ""
AUTHOR_SAVE_AS = ""
CATEGORY_SAVE_AS = ""
TAG_SAVE_AS = ""

FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

RELATIVE_URLS = True
DEFAULT_PAGINATION = False

PLUGIN_PATHS = ["plugins"]
PLUGINS = ["vetnet_data", "sitemap"]
SITEMAP = {
    "format": "xml",
    "exclude": ["portal/", "members/"],
    "priorities": {"articles": 0.5, "pages": 0.6, "indexes": 0.6},
    "changefreqs": {"articles": "monthly", "pages": "monthly", "indexes": "weekly"},
}
