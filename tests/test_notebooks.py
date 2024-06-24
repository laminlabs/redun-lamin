from pathlib import Path

import nbproject_test as test


def test_notebooks():
    docs_folder = Path(__file__).parents[1] / "docs/"
    test.execute_notebooks(
        docs_folder, write=True, print_cells=True, print_outputs=True
    )
