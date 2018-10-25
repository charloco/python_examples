import os
import sys
import pkg_resources
import operator

def main(argv=None):
    v=pkg_resources.iter_entry_points("entry_points_iter")
    l = list(map(operator.attrgetter("module_name"),v))
    print l
