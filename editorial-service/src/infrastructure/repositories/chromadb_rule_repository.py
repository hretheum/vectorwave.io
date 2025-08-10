"""
Infrastructure Repository: ChromaDBRuleRepository
Production implementation using ChromaDB Python SDK (HttpClient).

Notes:
- Uses SDK `collection.query()` and `collection.get()` with metadata filters
- Returns only rules with constructed chromadb_origin_metadata
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import chromadb  # type: ignore
    from chromadb.config import Settings  # type: ignore
except Exception as e:  # pragma: no cover
    raise RuntimeError(f"ChromaDB SDK import failed: {e}")
import structlog

from ...domain.entities.validation_rule import ValidationRule, RuleType, RuleSeverity
from ...domain.entities.validation_request import CheckpointType
from ...domain.interfaces.rule_repository import IRuleRepository


logger = structlog.get_logger()


class ChromaDBRuleRepository(IRuleRepository):
    """ChromaDB-backed rule repository (HTTP).

    Uses metadata filters to select appropriate rules for each workflow.
    """

    def __init__(self, host: Optional[str] = None, port: Optional[int] = None) -> None:
        self.host: str = host or os.getenv("CHROMADB_HOST", "localhost")
        self.port: int = int(port or os.getenv("CHROMADB_PORT", "8000"))

        # SDK client
        self._client = None

        # Collections used by editorial validation
        self.style_collection: str = "style_editorial_rules"
        self.platform_collection: str = "publication_platform_rules"

    # --- Public API ---
    async def get_comprehensive_rules(self, content: str) -> List[ValidationRule]:
        """Return 8-12 rules across style and platform dimensions."""
        style_rules = await self._fetch_by_where(
            self.style_collection, where=None, n_results=8, query_text=content
        )
        platform_rules = await self._fetch_by_where(
            self.platform_collection, where=None, n_results=6, query_text=content
        )
        merged = self._merge_and_balance(style_rules, platform_rules, target_min=8, target_max=12)
        if not merged:
            logger.error("comprehensive_selection_empty", note="No rules returned from ChromaDB")
            raise RuntimeError("No comprehensive rules available from ChromaDB")
        logger.info(
            "Comprehensive rule selection",
            style=len(style_rules),
            platform=len(platform_rules),
            selected=len(merged),
        )
        return merged

    async def get_selective_rules(self, content: str, checkpoint: CheckpointType) -> List[ValidationRule]:
        """Return 3-4 checkpoint-specific rules, prioritizing critical/high severity."""
        # Normalize checkpoint to metadata convention (underscore)
        checkpoint_meta = str(checkpoint.value).replace("-", "_")
        where = {"checkpoint": checkpoint_meta}
        style_rules = await self._fetch_by_where(
            self.style_collection, where=where, n_results=8, query_text=content
        )
        platform_rules = await self._fetch_by_where(
            self.platform_collection, where=where, n_results=6, query_text=content
        )
        candidates = style_rules + platform_rules
        # Fallback: if checkpoint-filtered returns too few, broaden search without checkpoint but keep checkpointed first
        if len(candidates) < 3:
            logger.warning("checkpoint_filter_empty_fallback", checkpoint=checkpoint.value)
            style_rules = await self._fetch_by_where(
                self.style_collection, where=None, n_results=8, query_text=content
            )
            platform_rules = await self._fetch_by_where(
                self.platform_collection, where=None, n_results=6, query_text=content
            )
            candidates = style_rules + platform_rules
        selected = self._prioritize_by_severity(candidates, target=4)
        if len(selected) < 3:
            remaining = [r for r in candidates if r not in selected]
            selected += remaining[: (3 - len(selected))]
        if not selected:
            logger.error("selective_selection_empty", checkpoint=checkpoint.value, note="No rules returned from ChromaDB")
            raise RuntimeError("No selective rules available from ChromaDB for checkpoint")
        logger.info(
            "Selective rule selection",
            checkpoint=checkpoint.value,
            style=len(style_rules),
            platform=len(platform_rules),
            selected=len(selected),
        )
        return selected[:4]

    async def get_rules_by_type(self, rule_type: RuleType, limit: Optional[int] = None) -> List[ValidationRule]:
        where = {"rule_type": rule_type.value}
        style = await self._fetch_by_where(self.style_collection, where=where, n_results=limit or 10)
        platform = await self._fetch_by_where(self.platform_collection, where=where, n_results=limit or 10)
        combined = (style + platform)[: (limit or len(style) + len(platform))]
        return combined

    async def get_rules_by_severity(self, severity: RuleSeverity, limit: Optional[int] = None) -> List[ValidationRule]:
        where = {"severity": severity.value}
        style = await self._fetch_by_where(self.style_collection, where=where, n_results=limit or 10)
        platform = await self._fetch_by_where(self.platform_collection, where=where, n_results=limit or 10)
        combined = (style + platform)[: (limit or len(style) + len(platform))]
        return combined

    async def search_rules(
        self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None
    ) -> List[ValidationRule]:
        where = filters or None
        style = await self._fetch_by_where(self.style_collection, where=where, n_results=limit, query_text=query)
        platform = await self._fetch_by_where(self.platform_collection, where=where, n_results=limit, query_text=query)
        combined = (style + platform)[:limit]
        return combined

    async def get_rule_by_id(self, rule_id: str) -> Optional[ValidationRule]:
        where = {"rule_id": rule_id}
        for collection in (self.style_collection, self.platform_collection):
            rules = await self._fetch_by_where(collection, where=where, n_results=1)
            if rules:
                return rules[0]
        return None

    async def get_collection_stats(self) -> Dict[str, Any]:
        try:
            client = self._ensure_client()
            # Best-effort availability flag
            return {"sdk_available": client is not None, "host": self.host, "port": self.port}
        except Exception as e:
            return {"sdk_available": False, "error": str(e)}

    async def health_check(self) -> bool:
        try:
            self._ensure_client()
            return True
        except Exception:
            return False

    # --- Internal helpers ---
    async def _fetch_by_where(
        self,
        collection: str,
        where: Optional[Dict[str, Any]] = None,
        n_results: int = 10,
        query_text: Optional[str] = None,
    ) -> List[ValidationRule]:
        """Query ChromaDB using Python SDK (preferred)."""
        col = self._ensure_client().get_or_create_collection(name=collection)
        rules: List[ValidationRule] = []
        try:
            # Prefer metadata-based filtering to avoid embedding dependency
            res = col.get(where=where, limit=n_results, include=["metadatas", "documents"])  # type: ignore[arg-type]
            ids = res.get("ids", []) or []
            metadatas = res.get("metadatas", []) or []
            documents = res.get("documents", []) or []
            if not metadatas and query_text:
                # Fallback to similarity query if no direct matches
                res = col.query(
                    query_texts=[query_text],
                    where=where,
                    n_results=n_results,
                    include=["metadatas", "documents"],
                )
                ids_groups = res.get("ids", []) or []
                metas_groups = res.get("metadatas", []) or []
                docs_groups = res.get("documents", []) or []
                ids = ids_groups[0] if ids_groups else []
                metadatas = metas_groups[0] if metas_groups else []
                documents = docs_groups[0] if docs_groups else []
            for idx, meta in enumerate(metadatas):
                rid = ids[idx] if idx < len(ids) else f"{collection}_{idx:04d}"
                doc = documents[idx] if idx < len(documents) else ""
                rules.append(self._metadata_to_rule(collection, rid, meta, doc))
        except Exception as e:
            logger.error("chroma_sdk_query_failed", error=str(e), collection=collection)
        return rules

    def _parse_query_response(self, collection: str, data: Dict[str, Any]) -> List[ValidationRule]:
        # Not used in SDK path; kept for completeness if needed in future
        ids_groups = data.get("ids", []) or []
        metas_groups = data.get("metadatas", []) or []
        docs_groups = data.get("documents", []) or []
        ids = ids_groups[0] if ids_groups else []
        metadatas = metas_groups[0] if metas_groups else []
        documents = docs_groups[0] if docs_groups else []
        rules: List[ValidationRule] = []
        for idx, meta in enumerate(metadatas):
            rid = ids[idx] if idx < len(ids) else f"{collection}_{idx:04d}"
            doc = documents[idx] if idx < len(documents) else ""
            rules.append(self._metadata_to_rule(collection, rid, meta, doc))
        return rules

    def _parse_get_response(self, collection: str, data: Dict[str, Any]) -> List[ValidationRule]:
        # Not used in SDK path; kept for completeness if needed in future
        ids = data.get("ids", []) or []
        metadatas = data.get("metadatas", []) or []
        documents = data.get("documents", []) or []
        rules: List[ValidationRule] = []
        for idx, meta in enumerate(metadatas):
            rid = ids[idx] if idx < len(ids) else f"{collection}_{idx:04d}"
            doc = documents[idx] if idx < len(documents) else ""
            rules.append(self._metadata_to_rule(collection, rid, meta, doc))
        return rules

    def _metadata_to_rule(self, collection: str, doc_id: str, meta: Dict[str, Any], document_text: str) -> ValidationRule:
        rule_id = str(meta.get("rule_id") or doc_id)
        rule_name = str(meta.get("rule_name") or meta.get("title") or "Unnamed Rule")
        description = str(meta.get("description") or document_text or "")
        rule_type = self._safe_rule_type(meta.get("rule_type"))
        severity = self._safe_rule_severity(meta.get("severity"))
        chroma_meta = {
            "collection_name": collection,
            "document_id": doc_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
        for extra in ("checkpoint", "platform", "workflow", "rule_category"):
            if meta.get(extra) is not None:
                chroma_meta[extra] = meta.get(extra)
        return ValidationRule(
            rule_id=rule_id,
            rule_name=rule_name,
            rule_type=rule_type,
            description=description,
            severity=severity,
            collection_source=collection,
            chromadb_origin_metadata=chroma_meta,
        )

    def _safe_rule_type(self, value: Optional[str]) -> RuleType:
        try:
            if value:
                return RuleType(value)
        except Exception:
            pass
        return RuleType.CONTENT

    def _safe_rule_severity(self, value: Optional[str]) -> RuleSeverity:
        try:
            if value:
                return RuleSeverity(value)
        except Exception:
            pass
        return RuleSeverity.MEDIUM

    def _merge_and_balance(self, style: List[ValidationRule], platform: List[ValidationRule], target_min: int, target_max: int) -> List[ValidationRule]:
        style_sorted = self._prioritize_by_severity(style, target=len(style))
        platform_sorted = self._prioritize_by_severity(platform, target=len(platform))
        merged: List[ValidationRule] = []
        si = pi = 0
        while len(merged) < target_max and (si < len(style_sorted) or pi < len(platform_sorted)):
            if si < len(style_sorted):
                merged.append(style_sorted[si])
                si += 1
            if len(merged) >= target_max:
                break
            if pi < len(platform_sorted):
                merged.append(platform_sorted[pi])
                pi += 1
        if len(merged) < target_min:
            remaining = style_sorted[si:] + platform_sorted[pi:]
            merged += remaining[: (target_min - len(merged))]
        return merged[:target_max]

    def _prioritize_by_severity(self, rules: List[ValidationRule], target: int) -> List[ValidationRule]:
        priority = {RuleSeverity.CRITICAL: 0, RuleSeverity.HIGH: 1, RuleSeverity.MEDIUM: 2, RuleSeverity.LOW: 3, RuleSeverity.INFO: 4}
        sorted_rules = sorted(rules, key=lambda r: priority.get(r.severity, 3))
        return sorted_rules[:target]

    # No mock fallback allowed by project rules

    def _ensure_client(self):
        if self._client is None:
            self._client = chromadb.HttpClient(
                host=self.host,
                port=self.port,
                settings=Settings(allow_reset=True),
            )
        return self._client
