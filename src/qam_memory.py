"""
QAM Memory — Hierarchical Zoom Memory (D0–D8) with Integrity & SYnc Verification
================================================================================
Provides a deterministic classical memory container across the 9 microscope-memory
zoom levels (D0..D8, SHA-256 + Merkle root) paired with a Loschmidt-echo SYnc
verification record.

Evidence boundary:
  Classical payload storage and Merkle integrity run deterministically on CPU.
  The paired SYnc check records whether the verification ran on real QPU hardware
  ("quantum") or local StatevectorSampler ("simulated"). Classical strings are
  not stored inside superconducting qubits.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from src.qam_core import QAM

NUM_ZOOM_LEVELS = 9  # D0..D8 (9 levels)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def compute_merkle_root(leaves: List[str]) -> str:
    """Compute a deterministic binary Merkle root over hex-encoded leaf digests."""
    if not leaves:
        return _sha256_hex(b"")
    layer = list(leaves)
    while len(layer) > 1:
        if len(layer) % 2 == 1:
            layer.append(layer[-1])
        next_layer: List[str] = []
        for i in range(0, len(layer), 2):
            combined = (layer[i] + layer[i + 1]).encode("ascii")
            next_layer.append(_sha256_hex(combined))
        layer = next_layer
    return layer[0]


class QAMMemory:
    """9-level (D0–D8) hierarchical memory store paired with QAM SYnc verification."""

    def __init__(
        self,
        token: Optional[str] = None,
        backend: str = "ibm_kingston",
        local: bool = False,
    ) -> None:
        self.qam = QAM(token=token, backend=backend, local=local)
        self._store: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def _normalize_depth(depth: int) -> int:
        if not (0 <= depth < NUM_ZOOM_LEVELS):
            raise ValueError(
                f"depth must be in D0..D8 (0..{NUM_ZOOM_LEVELS - 1}), got {depth}"
            )
        return depth

    @staticmethod
    def _build_zoom_projections(text: str) -> List[str]:
        """Create deterministic D0 (coarse summary) → D8 (full fidelity) projections."""
        if not text:
            return ["" for _ in range(NUM_ZOOM_LEVELS)]
        n = len(text)
        projections: List[str] = []
        for d in range(NUM_ZOOM_LEVELS):
            if d == NUM_ZOOM_LEVELS - 1:
                projections.append(text)
            else:
                keep = max(1, round(n * ((d + 1) / NUM_ZOOM_LEVELS)))
                projections.append(text[:keep])
        return projections

    def store_quantum_memory(
        self,
        data: str,
        depth: int = 8,
        key: Optional[str] = None,
        qubits: int = 1,
        shots: int = 1024,
    ) -> Dict[str, Any]:
        """
        Store `data` across zoom levels D0..D8 with Merkle integrity and run a
        paired QAM Loschmidt Echo verification.
        """
        norm_depth = self._normalize_depth(depth)
        entry_key = key if key is not None else data
        projections = self._build_zoom_projections(data)
        leaf_hashes = [
            _sha256_hex(f"D{lvl}:{proj}".encode("utf-8"))
            for lvl, proj in enumerate(projections)
        ]
        merkle_root = compute_merkle_root(leaf_hashes)
        qam_result = self.qam.sync_operation(qubits=qubits, shots=shots)

        record = {
            "key": entry_key,
            "data": data,
            "depth": norm_depth,
            "zoom_level": f"D{norm_depth}",
            "projections": projections,
            "leaf_hashes": leaf_hashes,
            "merkle_root": merkle_root,
            "qam_result": qam_result,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": "store",
        }
        self._store[entry_key] = record

        return {
            "key": entry_key,
            "data": projections[norm_depth],
            "depth": norm_depth,
            "zoom_level": f"D{norm_depth}",
            "merkle_root": merkle_root,
            "qam_result": qam_result,
            "timestamp": record["timestamp"],
            "operation": "store",
        }

    def recall_quantum_memory(self, query: str, depth: int = 8) -> Dict[str, Any]:
        """Recall a stored entry at zoom level D0..D8 and verify Merkle integrity."""
        norm_depth = self._normalize_depth(depth)
        record = self._store.get(query)
        now_iso = datetime.now(timezone.utc).isoformat()

        if record is None:
            return {
                "query": query,
                "depth": norm_depth,
                "zoom_level": f"D{norm_depth}",
                "found": False,
                "verified": False,
                "result": None,
                "timestamp": now_iso,
                "operation": "recall",
            }

        recomputed_leaves = [
            _sha256_hex(f"D{lvl}:{proj}".encode("utf-8"))
            for lvl, proj in enumerate(record["projections"])
        ]
        recomputed_root = compute_merkle_root(recomputed_leaves)
        verified = recomputed_root == record["merkle_root"]

        return {
            "query": query,
            "depth": norm_depth,
            "zoom_level": f"D{norm_depth}",
            "found": True,
            "verified": verified,
            "merkle_root": recomputed_root,
            "result": record["projections"][norm_depth],
            "sync_result_type": record["qam_result"].get("result_type"),
            "timestamp": now_iso,
            "operation": "recall",
        }


if __name__ == "__main__":
    qm = QAMMemory(local=True)
    print(qm.store_quantum_memory("QAM_TEST_DATA", depth=8))
    print(qm.recall_quantum_memory("QAM_TEST_DATA", depth=8))
