# New Body — AstroNVIM config

A drop-in [AstroNVIM](https://astronvim.com) (v4) configuration tuned for the
New Body control plane: Python (`src/new_body`) + Rust (`rust/`) with the same
lint/format rules as CI.

## Install

This `nvim/` folder is a complete Neovim config. Either:

```bash
# Option A: replace your personal config
ln -sfn "$(pwd)/nvim" ~/.config/nvim

# Option B: keep it isolated and launch on demand
NVIM_APPNAME=nvim nvim        # when nvim/ lives at ~/.config/nvim
```

AstroCommunity must be installed (the starter provides it). On first launch,
run `:Lazy sync` to fetch plugins.

## What it configures

| File | Purpose |
| --- | --- |
| `init.lua` | AstroCore options: 4-space tabs, `colorcolumn=88` (ruff/black width) |
| `lua/community.lua` | Extra plugins: `rustaceanvim`, `venv-selector.nvim` |
| `lua/plugins/rust.lua` | rust-analyzer via rustaceanvim (clippy as check, all features) |
| `lua/plugins/python.lua` | basedpyright (standard type checking) + venv picker |
| `lua/plugins/formatting.lua` | conform: `ruff_format`+`black` (py), `rustfmt`, `stylua` |
| `lua/plugins/project.lua` | `:make` → `make test-all` (runs both suites) |

## Usage

- Format on save is provided by AstroNvim; `:ConformInfo` shows formatters.
- `:make` (or the build keymap) runs `make test-all`, which executes `pytest`
  and `cargo test` and loads failures into the quickfix list.
- Open `docs/ARCHITECTURE.md` for the extension-point contract when adding
  subsystems in either language.
