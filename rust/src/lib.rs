//! Quantum Anchored Memory (QAM) — Rust Core
//!
//! Provides deterministic classical building blocks paired with QAM hardware
//! verification:
//!   1. `WavePacket`: ψ(t) = A·exp(-γ·t)·cos(2π·f·t + φ) and 2-qubit RY+CNOT
//!      probability encoding/decoding (`scs-quantum` bridge).
//!   2. `ZoomHierarchy`: 9-level (D0..D8) memory projections with deterministic
//!      Merkle root integrity verification.
//!   3. `SyncAudit`: Wilson 95% confidence interval and Shannon entropy
//!      evaluation for QPU Loschmidt Echo bitstring counts.

use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::f64::consts::PI;

pub const NUM_ZOOM_LEVELS: usize = 9;

/// Wavepacket representation ψ(t) = A · exp(-γ·t) · cos(2π·f·t + φ).
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct WavePacket {
    pub amplitude: f64,
    pub gamma: f64,
    pub frequency: f64,
    pub phase: f64,
}

/// Ideal measurement probabilities P(q0 = 1) for the 3-circuit quantum bridge.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct EncodedProbabilities {
    pub p_amplitude_one: f64,
    pub p_frequency_one: f64,
    pub p_phase_one: f64,
}

impl WavePacket {
    /// Evaluate ψ(t) at time `t`.
    pub fn evaluate(&self, t: f64) -> f64 {
        self.amplitude * (-self.gamma * t).exp() * (2.0 * PI * self.frequency * t + self.phase).cos()
    }

    /// Encode (A, f, φ) into ideal Z-basis probabilities via RY / RY+CNOT circuits.
    pub fn encode_probabilities(&self) -> EncodedProbabilities {
        let p_a = (self.amplitude / 2.0).sin().powi(2);
        let p_f = (PI * self.frequency).sin().powi(2);
        let p_phi = (self.phase / 2.0).sin().powi(2);
        EncodedProbabilities {
            p_amplitude_one: p_a,
            p_frequency_one: p_f,
            p_phase_one: p_phi,
        }
    }

    /// Decode (A ∈ [0, π], f ∈ [0, 0.5], φ ∈ [0, π]) from measured P(q0 = 1) values.
    pub fn decode_probabilities(probs: EncodedProbabilities, gamma: f64) -> Self {
        let clamp01 = |x: f64| x.clamp(0.0, 1.0);
        let p_a0 = clamp01(1.0 - clamp01(probs.p_amplitude_one));
        let p_f1 = clamp01(probs.p_frequency_one);
        let p_p1 = clamp01(probs.p_phase_one);

        let amplitude = 2.0 * p_a0.sqrt().acos();
        let frequency = p_f1.sqrt().asin() / PI;
        let phase = 2.0 * p_p1.sqrt().asin();

        Self {
            amplitude,
            gamma,
            frequency,
            phase,
        }
    }
}

/// Deterministic 64-bit FNV-1a digest rendered as 16-char lowercase hex.
pub fn fnv1a_hex(bytes: &[u8]) -> String {
    let mut hash: u64 = 0xcbf29ce484222325;
    for &b in bytes {
        hash ^= u64::from(b);
        hash = hash.wrapping_mul(0x100000001b3);
    }
    format!("{hash:016x}")
}

/// Compute a binary Merkle root over leaf digests.
pub fn compute_merkle_root(leaves: &[String]) -> String {
    if leaves.is_empty() {
        return fnv1a_hex(b"");
    }
    let mut layer: Vec<String> = leaves.to_vec();
    while layer.len() > 1 {
        if layer.len() % 2 == 1 {
            let last = layer.last().cloned().unwrap_or_default();
            layer.push(last);
        }
        let mut next = Vec::with_capacity(layer.len() / 2);
        for pair in layer.chunks(2) {
            let combined = format!("{}{}", pair[0], pair[1]);
            next.push(fnv1a_hex(combined.as_bytes()));
        }
        layer = next;
    }
    layer.remove(0)
}

/// 9-level (D0..D8) hierarchical memory entry with Merkle integrity.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ZoomEntry {
    pub key: String,
    pub projections: Vec<String>,
    pub merkle_root: String,
}

impl ZoomEntry {
    pub fn new(key: impl Into<String>, payload: &str) -> Self {
        let key_str = key.into();
        let chars: Vec<char> = payload.chars().collect();
        let n = chars.len();
        let mut projections = Vec::with_capacity(NUM_ZOOM_LEVELS);

        for d in 0..NUM_ZOOM_LEVELS {
            if n == 0 {
                projections.push(String::new());
            } else if d + 1 == NUM_ZOOM_LEVELS {
                projections.push(payload.to_string());
            } else {
                let keep = ((n * (d + 1) + (NUM_ZOOM_LEVELS / 2)) / NUM_ZOOM_LEVELS).max(1);
                projections.push(chars[..keep.min(n)].iter().collect());
            }
        }

        let leaves: Vec<String> = projections
            .iter()
            .enumerate()
            .map(|(lvl, proj)| fnv1a_hex(format!("D{lvl}:{proj}").as_bytes()))
            .collect();
        let merkle_root = compute_merkle_root(&leaves);

        Self {
            key: key_str,
            projections,
            merkle_root,
        }
    }

    pub fn recall(&self, depth: usize) -> Option<&str> {
        self.projections.get(depth).map(String::as_str)
    }

    pub fn verify_integrity(&self) -> bool {
        if self.projections.len() != NUM_ZOOM_LEVELS {
            return false;
        }
        let leaves: Vec<String> = self
            .projections
            .iter()
            .enumerate()
            .map(|(lvl, proj)| fnv1a_hex(format!("D{lvl}:{proj}").as_bytes()))
            .collect();
        compute_merkle_root(&leaves) == self.merkle_root
    }
}

/// Statistical audit summary for a QAM Loschmidt Echo measurement.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SyncAudit {
    pub job_id: String,
    pub backend: String,
    pub physical_qubit: usize,
    pub total_shots: u64,
    pub zero_hits: u64,
    pub success_rate: f64,
    pub wilson_95_ci: (f64, f64),
    pub shannon_entropy_bits: f64,
}

/// Compute Wilson score 95% confidence interval for `successes` out of `total`.
pub fn wilson_ci_95(successes: u64, total: u64) -> (f64, f64) {
    if total == 0 {
        return (0.0, 0.0);
    }
    let z = 1.959_963_984_540_054_f64;
    let n = total as f64;
    let p = (successes as f64) / n;
    let z2 = z * z;
    let denom = 1.0 + z2 / n;
    let center = (p + z2 / (2.0 * n)) / denom;
    let half = z * ((p * (1.0 - p) + z2 / (4.0 * n)) / n).sqrt() / denom;
    ((center - half).max(0.0), (center + half).min(1.0))
}

impl SyncAudit {
    pub fn from_counts(
        job_id: impl Into<String>,
        backend: impl Into<String>,
        physical_qubit: usize,
        qubits: usize,
        counts: &BTreeMap<String, u64>,
    ) -> Self {
        let total: u64 = counts.values().copied().sum();
        let zero_key = "0".repeat(qubits);
        let zero_hits = counts.get(&zero_key).copied().unwrap_or(0);
        let success_rate = if total > 0 {
            (zero_hits as f64) / (total as f64)
        } else {
            0.0
        };

        let mut entropy = 0.0_f64;
        if total > 0 {
            for &c in counts.values() {
                if c > 0 {
                    let p = (c as f64) / (total as f64);
                    entropy -= p * p.log2();
                }
            }
        }

        Self {
            job_id: job_id.into(),
            backend: backend.into(),
            physical_qubit,
            total_shots: total,
            zero_hits,
            success_rate,
            wilson_95_ci: wilson_ci_95(zero_hits, total),
            shannon_entropy_bits: entropy,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wavepacket_roundtrip_is_exact() {
        let wp = WavePacket {
            amplitude: 1.0,
            gamma: 0.1,
            frequency: 0.25,
            phase: 0.5,
        };
        let encoded = wp.encode_probabilities();
        let decoded = WavePacket::decode_probabilities(encoded, wp.gamma);
        assert!((decoded.amplitude - wp.amplitude).abs() < 1e-12);
        assert!((decoded.frequency - wp.frequency).abs() < 1e-12);
        assert!((decoded.phase - wp.phase).abs() < 1e-12);
    }

    #[test]
    fn zoom_hierarchy_d0_to_d8_integrity() {
        let mut entry = ZoomEntry::new("qam-test", "QuantumAnchoredMemoryPayload");
        assert_eq!(entry.projections.len(), 9);
        assert_eq!(entry.recall(8), Some("QuantumAnchoredMemoryPayload"));
        assert!(entry.verify_integrity());

        entry.projections[4].push('X');
        assert!(!entry.verify_integrity());
    }

    #[test]
    fn kingston_q91_hardware_audit_matches_measured_counts() {
        let mut counts = BTreeMap::new();
        counts.insert("0".to_string(), 1018);
        counts.insert("1".to_string(), 6);

        let audit = SyncAudit::from_counts("db7viu8r1c5c738ldhi0", "ibm_kingston", 91, 1, &counts);
        assert_eq!(audit.total_shots, 1024);
        assert!((audit.success_rate - 0.994_140_625).abs() < 1e-12);
        assert!(audit.wilson_95_ci.0 > 0.987 && audit.wilson_95_ci.1 < 0.998);
    }
}
