- Beamer presentations for computer structure course. Building slides into build directory. Based on powerpoint presentation.

- Remember that you cannot use linux breaks \\ inside TikZ nodes without setting align=center.

- If you need to build for debug, use -interaction=nonstopmode .

- Use relative positioning for TikZ nodes, e.g. (current page.center) or (current page.north east).

- Consider using xparse or pgfkeys for macros with many or optional arguments.

- When you claim successful compilation, ensure the log doesn't show any real errors.