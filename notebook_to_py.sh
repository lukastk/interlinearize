#!/bin/sh

jupytext --to py interlinearize.ipynb

echo '#!/usr/bin/env python3' | cat - interlinearize.py > temp && mv temp interlinearize.py

chmod +x interlinearize.py