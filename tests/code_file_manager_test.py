import os
import subprocess
from unittest import TestCase

import pytest

from mentat.code_file_manager import CodeFileManager
from mentat.config_manager import ConfigManager

config = ConfigManager()


def test_path_gitignoring(temp_testbed):
    gitignore_path = ".gitignore"
    testing_dir_path = "git_testing_dir"
    os.makedirs(testing_dir_path)

    # create 3 files, 2 ignored in gitignore, 1 not
    ignored_file_path_1 = os.path.join(testing_dir_path, "ignored_file_1.txt")
    ignored_file_path_2 = os.path.join(testing_dir_path, "ignored_file_2.txt")
    non_ignored_file_path = os.path.join(testing_dir_path, "non_ignored_file.txt")

    with open(gitignore_path, "w") as gitignore_file:
        gitignore_file.write("ignored_file_1.txt\nignored_file_2.txt")

    for file_path in [ignored_file_path_1, ignored_file_path_2, non_ignored_file_path]:
        with open(file_path, "w") as file:
            file.write("I am a file")

    # Run CodeFileManager on the git_testing_dir, and also explicitly pass in ignored_file_2.txt
    paths = [testing_dir_path, ignored_file_path_2]
    code_file_manager = CodeFileManager(paths, user_input_manager=None, config=config)

    expected_file_paths = [
        os.path.join(temp_testbed, ignored_file_path_2),
        os.path.join(temp_testbed, non_ignored_file_path),
    ]

    case = TestCase()
    case.assertListEqual(
        sorted(expected_file_paths), sorted(code_file_manager.file_paths)
    )


def test_ignore_non_text_files(temp_testbed):
    image_file_path = "image.jpg"
    with open(image_file_path, "w") as image_file:
        image_file.write("I am an image")
    code_file_manager = CodeFileManager(["./"], user_input_manager=None, config=config)
    assert (
        os.path.join(temp_testbed, image_file_path) not in code_file_manager.file_paths
    )


def test_no_paths_given(temp_testbed):
    # Get temp_testbed as the git root when given no paths
    code_file_manager = CodeFileManager([], user_input_manager=None, config=config)
    assert code_file_manager.git_root == temp_testbed


def test_paths_given(temp_testbed):
    # Get temp_testbed when given file in temp_testbed
    code_file_manager = CodeFileManager(
        ["scripts"], user_input_manager=None, config=config
    )
    assert code_file_manager.git_root == temp_testbed


def test_two_git_roots_given():
    # Exits when given 2 paths with separate git roots
    with pytest.raises(SystemExit) as e_info:
        os.makedirs("git_testing_dir")
        subprocess.run(["git", "init"], cwd="git_testing_dir")

        _ = CodeFileManager(
            ["./", "git_testing_dir"], user_input_manager=None, config=config
        )
    assert e_info.type == SystemExit


def test_glob_exclude(mocker, temp_testbed):
    # Makes sure glob exclude config works
    mock_glob_exclude = mocker.MagicMock()
    mocker.patch.object(ConfigManager, "file_exclude_glob_list", new=mock_glob_exclude)
    mock_glob_exclude.side_effect = [[os.path.join("glob_test", "**", "*.py")]]

    glob_exclude_path = os.path.join("glob_test", "bagel", "apple", "exclude_me.py")
    glob_include_path = os.path.join("glob_test", "bagel", "apple", "include_me.ts")
    os.makedirs(os.path.dirname(glob_exclude_path), exist_ok=True)
    with open(glob_exclude_path, "w") as glob_exclude_file:
        glob_exclude_file.write("I am excluded")
    os.makedirs(os.path.dirname(glob_include_path), exist_ok=True)
    with open(glob_include_path, "w") as glob_include_file:
        glob_include_file.write("I am included")

    code_file_manager = CodeFileManager(["."], user_input_manager=None, config=config)
    print(code_file_manager.file_paths)
    assert (
        os.path.join(temp_testbed, glob_exclude_path)
        not in code_file_manager.file_paths
    )
    assert os.path.join(temp_testbed, glob_include_path) in code_file_manager.file_paths


def test_code_file_checking(temp_testbed):
    # Makes sure non 'code' files aren't automatically picked up unless we request them
    noncode_path = "iamnotcode.notcode"
    noncode_path_requested = "iamalsonotcode.notcode"
    with open(noncode_path, "w") as f:
        f.write("I am an innocent non-code file!")
    with open(noncode_path_requested, "w") as f:
        f.write("I am an innocent non-code file that has been requested by the user!")

    paths = ["./", noncode_path_requested]
    code_file_manager = CodeFileManager(paths, user_input_manager=None, config=config)

    assert (
        os.path.join(temp_testbed, noncode_path_requested)
        in code_file_manager.file_paths
    )
    assert os.path.join(temp_testbed, noncode_path) not in code_file_manager.file_paths
    assert (
        os.path.join(temp_testbed, noncode_path)
        in code_file_manager.non_code_file_paths
    )


def test_utf8_encoding_checking(temp_testbed):
    # Makes sure we don't include non utf-8 encoded files, and we quit if user gives us one
    nonutf8_path = "iamnotutf8.py"
    with open(nonutf8_path, "wb") as f:
        # ASCII ranges from 0-127
        # After 128, UTF-8 requires additional code points to specify the character, so a single 128 is not valid UTF-8
        f.write(bytearray([128]))

    paths = ["./"]
    code_file_manager = CodeFileManager(paths, user_input_manager=None, config=config)
    assert os.path.join(temp_testbed, nonutf8_path) not in code_file_manager.file_paths

    with pytest.raises(KeyboardInterrupt) as e_info:
        nonutf8_path_requested = "iamalsonotutf8.py"
        with open(nonutf8_path_requested, "wb") as f:
            f.write(bytearray([128]))

        paths = [nonutf8_path_requested]
        _ = CodeFileManager(paths, user_input_manager=None, config=config)
    assert e_info.type == KeyboardInterrupt
