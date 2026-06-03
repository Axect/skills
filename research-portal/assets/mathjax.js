window.MathJax = {
  tex: {
    // arithmatex emits \(...\) and \[...\]; the extra $$ pair is a fallback for
    // display math nested inside list items, which arithmatex's block processor
    // leaves raw. Underscores stay intact in those blocks, so MathJax renders them.
    inlineMath: [["\\(", "\\)"]],
    displayMath: [["\\[", "\\]"], ["$$", "$$"]],
    processEscapes: true,
    processEnvironments: true
  },
  options: {
    // default skipHtmlTags already excludes pre/code/script, so scanning the
    // whole article body is safe and picks up both arithmatex spans and raw $$.
    skipHtmlTags: ["script", "noscript", "style", "textarea", "pre", "code", "annotation", "annotation-xml"]
  }
};

// Re-typeset on Material's instant navigation page swaps.
document$.subscribe(() => {
  if (window.MathJax && MathJax.typesetPromise) {
    MathJax.startup.output.clearCache();
    MathJax.typesetClear();
    MathJax.texReset();
    MathJax.typesetPromise();
  }
});
