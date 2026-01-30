from pathlib import Path
import unittest
from django.test import TestCase
from django.db import connection
import os
import sys
import django

BASE_DIR = Path(__file__).resolve().parent.parent

if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()


