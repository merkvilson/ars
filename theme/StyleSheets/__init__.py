import os

# Get the directory of this __init__.py file
BASE_DIR = os.path.dirname(__file__)


# Read the stylesheet
with open(os.path.join(BASE_DIR, "hierarchy.css"), "r", encoding="utf-8") as f:
    HIERARCHY_STYLE = f.read()

# Read the stylesheet
with open(os.path.join(BASE_DIR, "context_window.css"), "r", encoding="utf-8") as f:
    CONTEXT_WINDOW_STYLE = f.read()
