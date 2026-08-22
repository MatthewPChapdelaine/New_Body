-- Project-local settings: route :make to the combined test runner so
-- <leader> + build/quickfix works for both the Python and Rust suites.
return {
  {
    "AstroNvim/astrocore",
    opts = {
      autocmds = {
        new_body_makeprg = {
          {
            event = "FileType",
            pattern = { "python", "rust" },
            desc = "New Body: :make runs the combined Python + Rust test suite",
            callback = function()
              vim.opt_local.makeprg = "make test-all"
            end,
          },
        },
      },
    },
  },
}
