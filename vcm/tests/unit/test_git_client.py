import pytest
import git

from vcm.integrations.git_client import GitClient, GitNotInitializedError


@pytest.fixture
def temp_git_repo(tmp_path):
    """Fixture to create a clean temporary Git repository with an initial commit."""
    repo = git.Repo.init(tmp_path)
    readme = tmp_path / "README.md"
    readme.write_text("# Test Repo")
    repo.index.add(["README.md"])
    repo.index.commit("Initial commit")
    # Add a mock origin remote
    repo.create_remote("origin", "https://github.com/user/ml-test-repo.git")
    return repo, tmp_path


def test_ut_2_1_git_client_get_current_commit(temp_git_repo):
    """UT-2.1: GitClient.get_current_commit() returns valid commit hash."""
    repo, path = temp_git_repo
    client = GitClient(repo_path=str(path))
    commit = client.get_current_commit()

    assert isinstance(commit, str)
    assert len(commit) == 40
    assert commit == str(repo.head.commit.hexsha)


def test_ut_2_2_git_client_get_current_branch(temp_git_repo):
    """UT-2.2: GitClient.get_current_branch() returns branch name and handles detached HEAD."""
    repo, path = temp_git_repo
    client = GitClient(repo_path=str(path))
    branch = client.get_current_branch()
    assert branch in ("main", "master")

    # Detached HEAD state
    commit_hex = repo.head.commit.hexsha
    repo.git.checkout(commit_hex)
    detached_branch = client.get_current_branch()
    assert detached_branch == "HEAD (detached)" or detached_branch.startswith("HEAD")


def test_ut_2_3_git_client_get_remote_url(temp_git_repo):
    """UT-2.3: GitClient.get_remote_url() returns valid URL or None."""
    repo, path = temp_git_repo
    client = GitClient(repo_path=str(path))
    url = client.get_remote_url(remote_name="origin")
    assert url == "https://github.com/user/ml-test-repo.git"

    no_remote_url = client.get_remote_url(remote_name="nonexistent")
    assert no_remote_url is None


def test_ut_2_4_git_client_detect_uncommitted_changes(temp_git_repo):
    """UT-2.4: GitClient.has_uncommitted_changes() detects staged and unstaged changes."""
    repo, path = temp_git_repo
    client = GitClient(repo_path=str(path))

    assert not client.has_uncommitted_changes()

    # Create unstaged file
    new_file = path / "data.txt"
    new_file.write_text("unstaged data")
    assert client.has_uncommitted_changes()

    # Stage the file
    repo.index.add(["data.txt"])
    assert client.has_uncommitted_changes()

    # Commit the file -> should now be clean
    repo.index.commit("Add data.txt")
    assert not client.has_uncommitted_changes()


def test_ut_2_5_git_client_error_handling(tmp_path):
    """UT-2.5: GitClient handles errors gracefully when not a git repository."""
    non_git = tmp_path / "empty_dir"
    non_git.mkdir()
    client = GitClient(repo_path=str(non_git))

    with pytest.raises(GitNotInitializedError, match="Git repository not found"):
        client.get_current_commit()

    with pytest.raises(GitNotInitializedError):
        client.get_current_branch()

    assert not client.is_repo()
    assert client.get_safe_code_info().git_commit is None


def test_git_client_safe_info_with_repo(temp_git_repo):
    """Test get_safe_code_info on a real repo."""
    repo, path = temp_git_repo
    client = GitClient(repo_path=str(path))
    code_info = client.get_safe_code_info()
    assert code_info.git_commit is not None
    assert code_info.git_branch in ("main", "master")
    assert code_info.git_remote == "origin"
    assert code_info.git_url == "https://github.com/user/ml-test-repo.git"
