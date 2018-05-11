import os


def make_and_clear_directory(directory: str, remake: bool=True) -> None:
    """
    Create the supplied directory if needed and clear its contents.  Because this is a sufficiently dangerous function,
    it will only clear the contents of the directory if there is a file named 'generated' in it.

    :param directory: directory to create
    :param remake: Recreate the directory.  False means just remove it
    """
    import shutil

    safety_file = os.path.join(directory, "generated")
    if os.path.exists(directory):
        if not os.path.exists(safety_file):
            raise FileExistsError("{} not found in test directory".format(safety_file))
        shutil.rmtree(directory)
    if remake:
        os.makedirs(directory)
        with open(safety_file, "w") as f:
            f.write("Generated for safety.  Must be present for test to clear this directory.")
