from os import scandir


def tree_actions(path, actions, maxdepth=10):
    for entry in list(scantree(path, maxdepth=maxdepth)):
        if actions[0](entry):
            actions[1](entry)

def scantree(path, depth=0, maxdepth=10):
    for entry in scandir(path):
        if entry.is_dir(follow_symlinks=False) and depth < maxdepth:
            yield entry
            yield from scantree(entry.path, depth=depth+1, maxdepth=maxdepth)
        else:
            yield entry

