- Beamer presentations for computer structure course. Building slides into build directory. Based on powerpoint presentation.

- Remember that you cannot use linux breaks \\ inside TikZ nodes without setting align=center.

- If you need to build for debug, use -interaction=nonstopmode .

- Use relative positioning for TikZ nodes, e.g. (current page.center) or (current page.north east).

- Consider using xparse or pgfkeys for macros with many or optional arguments.

- Try to avoid using scale in TikZ nodes, as it can distort text. Instead, adjust font size or node dimensions directly.

- Use circuitikz package for drawing circuits. Not trapezoid.

- CRITICAL BUILD VERIFICATION: After every edit to .tex files, you MUST verify the build is error-free:
  1. Run: pdflatex -interaction=nonstopmode <file>.tex 2>&1 | grep -E "(^!|Error)"
  2. If ANY lines starting with "!" appear, the build has ERRORS even if PDF was generated
  3. "Output written" does NOT mean success - nonstopmode continues past errors
  4. Only declare success if grep returns NO results (empty output)
  5. Common gotcha: Using \\ in TikZ nodes requires align=center in the node style
