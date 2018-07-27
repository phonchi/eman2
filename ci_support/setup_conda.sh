#!/usr/bin/env bash

set -xe

# Configure conda
source ${HOME}/miniconda2/bin/activate root

conda install eman-deps=12.0 -c cryoem -c defaults -c conda-forge --yes
conda clean --all --yes
