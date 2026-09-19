"""Terminal output logger with privacy protection and secret masking."""

from __future__ import annotations

import io
import re
import sys
from datetime import datetime, timezone
from typing import Any, List, Optional, TextIO


class TerminalLogger:
    """Captures terminal output (stdout/stderr) with secret masking and privacy controls."""

    DEFAULT_MASK_PATTERNS = [
        r"(?i)(password\s*[:=]\s*)([^\s&]+)",
        r"(?i)(api[_-]?key\s*[:=]\s*)([^\s&]+)",
        r"(?i)(secret\s*[:=]\s*)([^\s&]+)",
        r"(?i)(token\s*[:=]\s*)([^\s&]+)",
        r"(?i)(github[_-]?token\s*[:=]\s*)([^\s&]+)",
        r"(?i)(bearer\s+)([a-zA-Z0-9_\-\.]+)",
        r"(?i)(AWS_SECRET_ACCESS_KEY\s*[:=]\s*)([^\s&]+)",
        r"(?i)(PRIVATE_KEY[^\n]+)",
    ]

    DEFAULT_EXCLUDE_PATTERNS = [
        r"^.*(?:npm install|pip install|pip3 install).*",
        r"^.*(?:\/bin\/).*$",
    ]

    def __init__(
        self,
        mask_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
        include_timestamps: bool = True,
    ) -> None:
        self.mask_patterns = [re.compile(p) for p in (mask_patterns or self.DEFAULT_MASK_PATTERNS)]
        self.exclude_patterns = [re.compile(p) for p in (exclude_patterns or self.DEFAULT_EXCLUDE_PATTERNS)]
        self.include_timestamps = include_timestamps
        self._buffer: List[str] = []
        self._is_capturing = False
        self._orig_stdout: Optional[TextIO] = None
        self._orig_stderr: Optional[TextIO] = None
        self._stdout_tee: Optional[_TeeStream] = None
        self._stderr_tee: Optional[_TeeStream] = None

    def mask_secrets(self, text: str) -> str:
        """Mask sensitive tokens, passwords, and API keys with ***MASKED***."""
        masked = text
        for pattern in self.mask_patterns:
            if pattern.groups >= 2:
                masked = pattern.sub(r"\1***MASKED***", masked)
            else:
                masked = pattern.sub("***MASKED***", masked)
        return masked

    def _should_exclude(self, line: str) -> bool:
        """Check if log line matches any noise exclusion patterns."""
        for pattern in self.exclude_patterns:
            if pattern.search(line):
                return True
        return False

    def log_line(self, line: str) -> None:
        """Record a single log line after masking and filtering."""
        clean_line = line.rstrip("\r\n")
        if not clean_line or self._should_exclude(clean_line):
            return

        masked_line = self.mask_secrets(clean_line)
        if self.include_timestamps:
            now_str = datetime.now(timezone.utc).astimezone().strftime("%H:%M:%S")
            formatted = f"{now_str} | {masked_line}"
        else:
            formatted = masked_line

        self._buffer.append(formatted)

    def start_capture(self) -> None:
        """Start capturing sys.stdout and sys.stderr."""
        if self._is_capturing:
            return

        self._orig_stdout = sys.stdout
        self._orig_stderr = sys.stderr

        self._stdout_tee = _TeeStream(self._orig_stdout, self.log_line)
        self._stderr_tee = _TeeStream(self._orig_stderr, self.log_line)

        sys.stdout = self._stdout_tee
        sys.stderr = self._stderr_tee
        self._is_capturing = True

    def stop_capture(self) -> str:
        """Stop capturing and restore standard streams, returning full captured log."""
        if not self._is_capturing:
            return self.get_log()

        if self._orig_stdout is not None:
            sys.stdout = self._orig_stdout
        if self._orig_stderr is not None:
            sys.stderr = self._orig_stderr

        self._is_capturing = False
        return self.get_log()

    def get_log(self) -> str:
        """Return the accumulated log buffer as a single string."""
        return "\n".join(self._buffer)

    def clear(self) -> None:
        """Clear all buffered logs."""
        self._buffer.clear()


class _TeeStream(io.TextIOBase):
    """Custom stream splitter to forward writes to real stream and logger callback."""

    def __init__(self, stream: TextIO, callback: Any) -> None:
        super().__init__()
        self._stream = stream
        self._callback = callback
        self._line_buffer = ""

    def write(self, s: str) -> int:
        if self._stream:
            self._stream.write(s)
            self._stream.flush()

        self._line_buffer += s
        while "\n" in self._line_buffer:
            line, self._line_buffer = self._line_buffer.split("\n", 1)
            self._callback(line)

        return len(s)

    def flush(self) -> None:
        if self._stream:
            self._stream.flush()
        if self._line_buffer:
            self._callback(self._line_buffer)
            self._line_buffer = ""

    def isatty(self) -> bool:
        return getattr(self._stream, "isatty", lambda: False)()
