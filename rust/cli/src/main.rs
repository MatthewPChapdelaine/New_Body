//! `new-body-rs` — Rust CLI for the New Body surrogate control plane.

use clap::{Parser, Subcommand};
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
    }
}
