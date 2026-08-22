-- New Body — AstroNVIM configuration (Python + Rust control plane)
--
-- Install (drop-in): copy this folder to ~/.config/nvim, or from the parent
-- of this folder run:  NVIM_APPNAME=nvim nvim
-- Requires AstroNvim (v4) + AstroCommunity. See nvim/README.md.

require("astrocore").setup({
  options = {
    opt = {
      number = true,
      relativenumber = true,
      termguicolors = true,
      tabstop = 4,
      softtabstop = 4,
      shiftwidth = 4,
      expandtab = true,
      colorcolumn = "88", -- matches ruff/black line-length
    },
  },
})
