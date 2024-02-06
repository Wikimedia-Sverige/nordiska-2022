# 100 000 Bildminnen

A collection of scripts and data connected to the 2022-2023 project *100 000 Bildminnen*. A project done together with, and with funding from, Nordiska museet.

Not included in this repo is `commons-diff`, the tool developed for extracting changes to file pages on Wikimedia Commons in support of roundtripping. This tool is instead provided in [its own repo](https://github.com/Wikimedia-Sverige/commons-diff/) where it has been developed with an aim to be useful beyond this project.

For the uploaded images see [Commons:Nordiska museet/100 000 Bildminnen](https://commons.wikimedia.org/wiki/Commons:Nordiska_museet/100_000_Bildminnen).

The final report for the project can be found at [100 000 Bildminnen - Slutrapport.pdf](https://commons.wikimedia.org/wiki/File:100_000_Bildminnen_-_Slutrapport.pdf).

## Structure

The repo is structured so that each script lives in a different directory. The directory contains the code of the script as well as a requirements file.

The directory may also contain a `output_data` subdirectory containing the final outputs from this scripts when run right after the end of the project. If this subdirectory exists it will also contain an `_inputs.md` file documenting the inputs used to produce each output.

## Scripts

Below is a very brief description of each script.

* **mediaviews**: Get all media-views/mediarequests for files in a Commons category during a provided time span.
* **wp_captions**: Get all images in a Commons category and for each get all global usages and associated captions.
* **deriv_detector**: Attempt to identify derivative files by analysing which other files link to files in a Commons category.
* **file_count**: Show the growth of a Commons category of files by analysing the upload dates of its category.
* **diff_stats**: Extract some statistics from the [commons-diff](https://github.com/Wikimedia-Sverige/commons-diff/) output files. The `output_data` directory also contains the final commons-diff output.

## Disclaimer

While many of the scripts have been generalised to be of use outside the context of this project they are primarilly provided here for convenience and documentation purposes. They are unlikely to be maintained and further development may take place in other repos.
