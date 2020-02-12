from os import scandir, DirEntry


def tree_actions(path, predicate=lambda entry: True, action=lambda entry: print(entry), maxdepth=10):
    """Walks a directory starting at path, and for each entry will
    take an action if the predicate function returns true"""
    for entry in scantree(path, maxdepth=maxdepth):
        if predicate(entry):
            action(entry)


def scantree(path, depth=0, maxdepth=10):
    for entry in scandir(path):
        if entry.is_dir(follow_symlinks=False) and depth < maxdepth:
            yield entry
            yield from scantree(entry.path, depth=depth + 1, maxdepth=maxdepth)
        else:
            yield entry

