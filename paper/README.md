# Overleaf Build Instructions

This folder contains an Overleaf-ready LaTeX project for the PCC-NIUC paper.

## Compile locally

- Use XeLaTeX + Biber:
  1. xelatex main
  2. biber main
  3. xelatex main
  4. xelatex main

The generated PDF is `main.pdf`.

## Compile on Overleaf

- Upload the entire `paper/` directory to Overleaf
- In Menu → Compiler, select `XeLaTeX`
- Ensure Bibliography tool is `Biber`
- Click Recompile

## Files
- `main.tex`: manuscript preamble and structure
- `abstract.tex`: abstract (auto-filled from PAPER.md)
- `content.tex`: main sections (auto-filled from PAPER.md)
- `refs.bib`: references extracted from docs/lit_review.md

If a citation key is missing, add a BibTeX entry to `refs.bib` and recompile.

