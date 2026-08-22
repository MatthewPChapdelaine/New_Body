-- Formatting: ruff (format) + black for Python, rustfmt for Rust, stylua for
-- Lua. Conform is bundled with AstroNvim.
return {
  {
    "conform.nvim",
    opts = {
      formatters_by_ft = {
        python = { "ruff_format", "black" },
        rust = { "rustfmt" },
        lua = { "stylua" },
      },
    },
  },
}
