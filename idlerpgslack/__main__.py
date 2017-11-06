# -*- coding: utf-8 -*-
"""Command-Line Interface Main Wrapper

Calls the CLI main function. This wrapper is to allow the script to be called directly from the
command-line, or as a python module.
"""

from .cli import main

if __name__ == '__main__':
    main()
