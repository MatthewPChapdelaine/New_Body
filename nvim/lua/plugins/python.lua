-- Python tooling: basedpyright via AstroLSP, plus a virtualenv picker.
return {
  {
    "AstroNvim/astrolsp",
    opts = {
      servers = { "basedpyright" },
      config = {
        basedpyright = {
          settings = {
            basedpyright = {
              analysis = { typeCheckingMode = "standard" },
            },
          },
        },
      },
    },
  },
  {
    "linux-cultist/venv-selector.nvim",
    ft = { "python" },
    dependencies = { "neovim/nvim-lspconfig" },
  },
}
