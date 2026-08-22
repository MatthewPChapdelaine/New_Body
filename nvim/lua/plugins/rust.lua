-- Rust tooling: rustaceanvim wrapping rust-analyzer, clippy as the check
-- command, and all-features cargo resolution.
return {
  {
    "mrcjkb/rustaceanvim",
    version = "^6",
    ft = { "rust" },
    config = function()
      require("rustaceanvim").setup({
        server = {
          default_settings = {
            ["rust-analyzer"] = {
              cargo = { allFeatures = true },
              check = { command = "clippy" },
            },
          },
        },
      })
    end,
  },
}
