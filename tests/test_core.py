import unittest
import sys
print(sys.path)
import agentstr

from agentstr.core import add

def test_add():
    assert add(2, 3) == 5

