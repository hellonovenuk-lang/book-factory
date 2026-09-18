"""The asset registry.

Illustration assets and locked visual references. Structurally the same
draft/approve discipline as pages, because the failure mode is the same:
approved artwork being quietly replaced.
"""

from __future__ import annotations

from pathlib import Path

from bookfactory import SCHEMA_VERSION
from bookfactory.core import clock, schema
from bookfactory.core.errors import ValidationError
from bookfactory.core.jsonio import read_json, write_json
from bookfactory.core.models import AssetRecord


class AssetRegistry:
    def __init__(self, book_id: str, assets: list[AssetRecord] | None = None,
                 *, updated_at: str | None = None) -> None:
        self.book_id = book_id
        self.assets: list[AssetRecord] = assets or []
        self.updated_at = updated_at or clock.timestamp()

    @classmethod
    def empty(cls, book_id: str) -> "AssetRegistry":
        return cls(book_id)

    @classmethod
    def load(cls, path: str | Path) -> "AssetRegistry":
        data = read_json(path)
        schema.validate("asset", data, context=str(path))
        return cls(
            book_id=data["book_id"],
            assets=[AssetRecord.from_dict(a) for a in data.get("assets", [])],
            updated_at=data.get("updated_at"),
        )

    def to_dict(self) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "book_id": self.book_id,
            "updated_at": self.updated_at,
            "assets": [a.to_dict() for a in sorted(self.assets, key=lambda a: a.asset_id)],
        }

    def save(self, path: str | Path) -> Path:
        self.updated_at = clock.timestamp()
        data = self.to_dict()
        schema.validate("asset", data, context=str(path))
        return write_json(path, data)

    # -- access -----------------------------------------------------------
    def find(self, asset_id: str) -> AssetRecord | None:
        for asset in self.assets:
            if asset.asset_id == asset_id:
                return asset
        return None

    def get(self, asset_id: str) -> AssetRecord:
        asset = self.find(asset_id)
        if asset is None:
            known = ", ".join(a.asset_id for a in self.assets[:10]) or "<none>"
            raise ValidationError(
                f"Asset {asset_id!r} is not in the asset registry",
                remedy=f"Known assets: {known}. Register it with `bookfactory asset add`.",
            )
        return asset

    def add(self, asset: AssetRecord) -> AssetRecord:
        if self.find(asset.asset_id):
            raise ValidationError(
                f"Asset {asset.asset_id!r} already exists",
                remedy="Asset ids are unique within a book.",
            )
        self.assets.append(asset)
        return asset

    def of_kind(self, *kinds: str) -> list[AssetRecord]:
        return [a for a in self.assets if a.kind in kinds]

    def for_page(self, page_id: str) -> list[AssetRecord]:
        return [a for a in self.assets if a.page_id == page_id]

    def references(self) -> list[AssetRecord]:
        return [a for a in self.assets if a.is_reference]

    def locked_references(self) -> list[AssetRecord]:
        return [a for a in self.references() if a.locked and a.is_approved]

    def __iter__(self):
        return iter(sorted(self.assets, key=lambda a: a.asset_id))

    def __len__(self) -> int:
        return len(self.assets)

    def counts(self) -> dict:
        counts = {"planned": 0, "draft_submitted": 0, "approved": 0, "rejected": 0}
        for asset in self.assets:
            counts[asset.status] = counts.get(asset.status, 0) + 1
        counts["total"] = len(self.assets)
        return counts

    def problems(self) -> list[str]:
        found: list[str] = []
        seen_paths: dict[str, str] = {}
        for asset in self:
            if asset.approved:
                path = asset.approved.path
                if path in seen_paths:
                    found.append(
                        f"filename collision: {asset.asset_id} and {seen_paths[path]} both claim {path}"
                    )
                seen_paths[path] = asset.asset_id
        return found
