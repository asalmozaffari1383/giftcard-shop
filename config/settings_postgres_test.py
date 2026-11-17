from .settings import *
from .settings import DATABASES as POSTGRES_DATABASES

DATABASES = {"default": {**POSTGRES_DATABASES["default"], "TEST": {"NAME": "test_alisan_shop"}}}
