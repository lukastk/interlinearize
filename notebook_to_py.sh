#!/bin/sh

jupytext --to py interlinearizer.ipynb

echo '#!/usr/bin/env python3' | cat - interlinearizer.py > temp && mv temp interlinearizer.py

chmod +x interlinearizer.py