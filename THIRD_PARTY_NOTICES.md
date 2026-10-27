# Third-party notices

Our own code is under the [MIT License](LICENSE). It relies on the projects below, each under its own license. None of their code is copied into this repository; they are installed as dependencies or called as services.

## Python dependencies

| Project | Use | License |
|---|---|---|
| [Playwright for Python](https://github.com/microsoft/playwright-python) | replays the clicks and captures the new app | Apache-2.0 |
| [OpenCV](https://github.com/opencv/opencv) (opencv-python-headless) | reads and writes video frames | Apache-2.0 (library), MIT (Python wheels) |
| [scikit-image](https://github.com/scikit-image/scikit-image) | SSIM | BSD-3-Clause |
| [SciPy](https://github.com/scipy/scipy) | one-to-one matching of components | BSD-3-Clause |
| [NumPy](https://github.com/numpy/numpy) | arrays | BSD-3-Clause |
| [pytest](https://github.com/pytest-dev/pytest) | tests (dev only) | MIT |

Playwright downloads its own Chromium build, which ships with its own license files.

## Meta models

| Model | Use | Terms |
|---|---|---|
| Muse Wonder | reads the video and writes the app spec | Meta API terms of the hackathon |
| Muse Code | writes and fixes the web app | Meta API terms of the hackathon |
| Muse Image | redraws pixelated or missing visuals | Meta API terms of the hackathon |
| SAM 3.1 | finds buttons, text fields and images on both sides | license in Meta's official SAM repository |

Images produced by Muse Image are covered by the same terms as the model that made them.

## Benchmark captures

`bench/data/` holds screenshots of nasa.gov, fema.gov and noaa.gov as archived in January and February 1999 by the [Internet Archive](https://web.archive.org/). Works of the US federal government are in the public domain (17 U.S.C. 105). If any item turns out to belong to a third party, tell us and we will remove it.

## Sample apps

The videos we resurrect are not part of this repository and keep their own rights. We only use our own old projects, open source apps, or sites whose owner agreed. See [samples/README.md](samples/README.md).
