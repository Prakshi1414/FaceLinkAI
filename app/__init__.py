# Why do we create __init__.py file?

# 1. It tells Python that this folder is a "package"
#    (not just a normal folder)

# 2. It allows importing files from that folder
#    Example:
#    from app.config import settings

# 3. Without __init__.py:
#    Python may not recognize the folder as a module
#    which can cause "ModuleNotFoundError" or IDE warnings

# 4. This file can be completely empty
#    its only purpose is to mark the folder as a package

# Simple summary:
#  __init__.py makes a folder importable as a Python package