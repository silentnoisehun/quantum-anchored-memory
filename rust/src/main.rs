use qam::{SyncAudit, WavePacket, ZoomEntry};
use std::collections::BTreeMap;

fn main() {
    println!("QAM Rust Core v0.2.0 — Classical Bridge & Hardware Audit");
    println!("========================================================");

    // 1. WavePacket encode/decode roundtrip (CLASSICAL verification)
    let wp = WavePacket {
        amplitude: 1.0,
        gamma: 0.1,
        frequency: 0.25,
        phase: 0.5,
    };
    let probs = wp.encode_probabilities();
    let decoded = WavePacket::decode_probabilities(probs, wp.gamma);
    println!(
        "[CLASSICAL] WavePacket roundtrip: A={:.4}-> {:.4}, f={:.4}-> {:.4}, phi={:.4}-> {:.4}",
        wp.amplitude, decoded.amplitude, wp.frequency, decoded.frequency, wp.phase, decoded.phase
    );

    // 2. D0..D8 hierarchical zoom store + Merkle integrity check
    let entry = ZoomEntry::new("qam_demo", "Quantum Anchored Memory D0-D8 Hierarchy");
    println!(
        "[CLASSICAL] D0..D8 Merkle root={} verified={}",
        entry.merkle_root,
        entry.verify_integrity()
    );

    // 3. Recompute audit statistics for measured ibm_kingston Job db7viu8r1c5c738ldhi0 (q91)
    let mut counts = BTreeMap::new();
    counts.insert("0".to_string(), 1018);
    counts.insert("1".to_string(), 6);
    let audit = SyncAudit::from_counts("db7viu8r1c5c738ldhi0", "ibm_kingston", 91, 1, &counts);

    println!("\n[HARDWARE RECORD RECOMPUTED]");
    println!(
        "{}",
        serde_json::to_string_pretty(&audit).unwrap_or_default()
    );
}
