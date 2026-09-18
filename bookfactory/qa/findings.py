"""QA finding types."""

from __future__ import annotations

from dataclasses import dataclass, field

ERROR = "error"
WARNING = "warning"
INFO = "info"


@dataclass
class Finding:
    level: str
    code: str
    message: str
    page_id: str | None = None
    asset_id: str | None = None
    remedy: str | None = None
    needs_human: bool = False

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "code": self.code,
            "message": self.message,
            "page_id": self.page_id,
            "asset_id": self.asset_id,
            "remedy": self.remedy,
            "needs_human": self.needs_human,
        }


@dataclass
class LayerResult:
    layer: str
    findings: list[Finding] = field(default_factory=list)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == WARNING]

    @property
    def status(self) -> str:
        if self.errors:
            return "fail"
        if self.warnings:
            return "warn"
        return "pass"

    def to_dict(self) -> dict:
        return {
            "layer": self.layer,
            "status": self.status,
            "findings": [f.to_dict() for f in self.findings],
        }

    def error(self, code: str, message: str, **kwargs) -> None:
        self.findings.append(Finding(ERROR, code, message, **kwargs))

    def warn(self, code: str, message: str, **kwargs) -> None:
        self.findings.append(Finding(WARNING, code, message, **kwargs))

    def info(self, code: str, message: str, **kwargs) -> None:
        self.findings.append(Finding(INFO, code, message, **kwargs))
