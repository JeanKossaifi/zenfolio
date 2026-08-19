import nbformat

from zenfolio.parsers.bibtex_parser import BibtexParser
from zenfolio.parsers.jupyter_parser import JupyterParser


def test_bibtex_display_decodes_latex_without_changing_citation(tmp_path):
    bib_path = tmp_path / "publications.bib"
    bib_path.write_text(
        r"""
@article{example,
  title={A Result \& a \#Tag},
  author={Kossaifi, Jean and Varoquaux, G{\"a}el},
  journal={Foundations and Trends{\textregistered} in Machine Learning},
  year={2026}
}
""".strip(),
        encoding="utf-8",
    )

    publication = BibtexParser("Kossaifi").parse_file(bib_path)[0]

    assert publication["title"] == "A Result & a #Tag"
    assert publication["authors"] == ["Jean Kossaifi", "Gäel Varoquaux"]
    assert publication["venue"] == "Foundations and Trends® in Machine Learning"
    assert r"\&" in publication["bibtex"]
    assert r"G{\"a}el" in publication["bibtex"]


def test_bibtex_incollection_uses_booktitle_as_venue(tmp_path):
    bib_path = tmp_path / "chapter.bib"
    bib_path.write_text(
        """
@incollection{chapter,
  title={A Book Chapter},
  author={Kossaifi, Jean},
  booktitle={Signal Processing and Machine Learning Theory},
  year={2024}
}
""".strip(),
        encoding="utf-8",
    )

    publication = BibtexParser().parse_file(bib_path)[0]

    assert publication["venue"] == "Signal Processing and Machine Learning Theory"


def test_bibtex_primary_url_only_targets_readable_paper_content(tmp_path):
    bib_path = tmp_path / "links.bib"
    bib_path.write_text(
        """
@article{paper,
  title={Paper},
  author={Kossaifi, Jean},
  journal={Journal},
  year={2026},
  doi={10.1000/example},
  pdf={https://example.test/paper.pdf},
  code={https://github.com/example/code}
}
@article{codeonly,
  title={Code Only},
  author={Kossaifi, Jean},
  journal={Journal},
  year={2025},
  code={https://github.com/example/code-only}
}
""".strip(),
        encoding="utf-8",
    )

    publications = BibtexParser().parse_file(bib_path)
    by_title = {publication["title"]: publication for publication in publications}

    assert by_title["Paper"]["primary_url"] == "https://doi.org/10.1000/example"
    assert by_title["Code Only"]["primary_url"] == ""


def test_notebook_prefers_image_over_plain_text_fallback(tmp_path):
    notebook_path = tmp_path / "figure.ipynb"
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                "make_figure()",
                outputs=[
                    nbformat.v4.new_output(
                        "display_data",
                        data={
                            "image/png": "YWJj",
                            "text/plain": (
                                "<matplotlib.figure.Figure at 0x123456>"
                            ),
                        },
                    )
                ],
            )
        ]
    )
    nbformat.write(notebook, notebook_path)

    content = JupyterParser().parse_file(notebook_path)["content"]

    assert "data:image/png;base64,YWJj" in content
    assert "matplotlib.figure.Figure" not in content
