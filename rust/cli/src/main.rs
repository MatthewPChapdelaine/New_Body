//! `new-body-rs` — Rust CLI for the New Body surrogate control plane.

use clap::{Parser, Subcommand};
use new_body_core::body::HumanTwin;
use new_body_core::raw::{Frame, PROTO_SENSORY};
use new_body_core::render;
use new_body_core::surrogate::Surrogate;

#[derive(Parser)]
#[command(
    name = "new-body-rs",
    about = "New Body surrogate control plane (Rust)"
)]
struct Cli {
    /// Surrogate identifier.
    #[arg(long, default_value = "Surrogate-01")]
    name: String,

    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand)]
enum Command {
    /// Print full infrastructure status.
    Status,
    /// Run link/power/ESD health check.
    Health,
    /// Encode + decode a sample raw binary frame (demonstrates the link layer).
    Frame,
    /// Emulate the full human body & mind as a structural digital twin.
    Human,
}

fn hex_encode(bytes: &[u8]) -> String {
    bytes
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect::<Vec<_>>()
        .join("")
}

fn main() {
    let cli = Cli::parse();
    let surrogate = Surrogate::factory_default(&cli.name);

    match cli.command {
        Command::Status => println!("{}", render::render_status(&surrogate)),
        Command::Health => {
            println!("{}", render::render_health(&surrogate));
            if !surrogate.is_healthy() {
                std::process::exit(1);
            }
        }
        Command::Frame => {
            let frame = Frame {
                protocol: PROTO_SENSORY,
                port: 3,
                timestamp_us: 1_234_567,
                payload: vec![0xDE, 0xAD, 0xBE, 0xEF],
            };
            let bytes = frame.encode();
            println!("encoded ({} bytes): {}", bytes.len(), hex_encode(&bytes));
            let decoded = Frame::decode(&bytes).expect("roundtrip");
            println!(
                "decoded: proto={} port={} ts={} payload={:?}",
                decoded.protocol, decoded.port, decoded.timestamp_us, decoded.payload
            );
        }
        Command::Human => {
            let twin = HumanTwin::factory_default(&cli.name);
            println!("{}", twin.summary());
            let frames = twin.emit_frames();
            println!(
                "\nEmitted {} raw Cat-8 frames carrying body + mind telemetry",
                frames.len()
            );
            if let Some(first) = frames.first() {
                println!("sample frame: {}", hex_encode(first));
            }
        }
    }
}
