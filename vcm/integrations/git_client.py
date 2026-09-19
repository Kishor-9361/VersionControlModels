"""Git client integration for VCM."""

from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional

try:
    import git
    from git.exc import InvalidGitRepositoryError, NoSuchPathError
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False
    git = None  # type: ignore

from vcm.models.metadata import CodeInfo

logger = logging.getLogger(__name__)


class GitNotInitializedError(Exception):
    """Raised when Git repository is not found."""
    pass


class GitClient:
    """Provides Git repository inspection for tracking code commits and branches."""

    def __init__(self, repo_path: str = ".") -> None:
        self.repo_path = os.path.abspath(repo_path)
        self._repo: Optional[git.Repo] = None

    def _get_repo(self) -> git.Repo:
        if not GIT_AVAILABLE:
            raise GitNotInitializedError("GitPython library is not installed")

        if self._repo is not None:
            return self._repo

        try:
            self._repo = git.Repo(self.repo_path, search_parent_directories=True)
            return self._repo
        except (InvalidGitRepositoryError, NoSuchPathError) as exc:
            raise GitNotInitializedError(
                f"Git repository not found in current or parent directories of {self.repo_path}"
            ) from exc

    def is_repo(self) -> bool:
        """Check if repo_path belongs to a valid Git repository."""
        try:
            self._get_repo()
            return True
        except (GitNotInitializedError, Exception):
            return False

    def get_current_commit(self) -> str:
        """Return the current HEAD commit hash (40-character hex string)."""
        repo = self._get_repo()
        try:
            return str(repo.head.commit.hexsha)
        except Exception as exc:
            raise GitNotInitializedError(f"Failed to get HEAD commit: {exc}") from exc

    def get_current_branch(self) -> str:
        """Return the current active branch name or 'HEAD (detached)'."""
        repo = self._get_repo()
        try:
            if repo.head.is_detached:
                return "HEAD (detached)"
            return str(repo.active_branch.name)
        except TypeError:
            return "HEAD (detached)"
        except Exception as exc:
            raise GitNotInitializedError(f"Failed to determine branch: {exc}") from exc

    def get_remote_url(self, remote_name: str = "origin") -> Optional[str]:
        """Return the clean remote URL for the specified remote, or None."""
        try:
            repo = self._get_repo()
            for remote in repo.remotes:
                if remote.name == remote_name:
                    url = str(remote.url)
                    # Strip any embedded basic-auth tokens (e.g. https://token@github.com/...)
                    clean_url = re.sub(r"://[^@]+@", "://", url)
                    return clean_url
            return None
        except Exception:
            return None

    def has_uncommitted_changes(self) -> bool:
        """Return True if there are staged, unstaged, or untracked changes."""
        try:
            repo = self._get_repo()
            # Staged changes (diff against HEAD)
            if repo.is_dirty(untracked_files=True):
                # Filter out .vcm/ or .vcmconfig.yaml changes if only those changed
                diffs = repo.index.diff(None)
                untracked = repo.untracked_files
                meaningful_untracked = [
                    f for f in untracked
                    if not f.startswith(".vcm") and not f.endswith(".vcm.json")
                ]
                meaningful_diffs = [
                    d.a_path for d in diffs
                    if d.a_path and not d.a_path.startswith(".vcm")
                ]
                return bool(meaningful_untracked or meaningful_diffs or repo.index.diff("HEAD"))
            return False
        except Exception:
            return False

    def get_safe_code_info(self, remote_name: str = "origin") -> CodeInfo:
        """Safely extract CodeInfo metadata without throwing errors on missing git repo."""
        try:
            if not self.is_repo():
                return CodeInfo()
            commit = self.get_current_commit()
            branch = self.get_current_branch()
            url = self.get_remote_url(remote_name)
            return CodeInfo(
                git_commit=commit,
                git_branch=branch,
                git_remote=remote_name if url else None,
                git_url=url,
            )
        except Exception as exc:
            logger.warning("Git metadata extraction failed gracefully: %s", exc)
            return CodeInfo()

    def get_diff(self, commit1: str, commit2: str) -> dict[str, Any]:
        """Compute git diff between two commits."""
        try:
            repo = self._get_repo()
            c1 = repo.commit(commit1)
            c2 = repo.commit(commit2)
            diff_index = c1.diff(c2)
            files_changed = [d.a_path or d.b_path for d in diff_index if d.a_path or d.b_path]
            return {
                "commit1": commit1,
                "commit2": commit2,
                "files_changed": files_changed,
            }
        except Exception:
            return {"commit1": commit1, "commit2": commit2, "files_changed": []}


def get_git_diff(commit1: str, commit2: str, repo_path: str = ".") -> dict[str, Any]:
    """Helper function to get git diff between two commits."""
    client = GitClient(repo_path=repo_path)
    return client.get_diff(commit1, commit2)
