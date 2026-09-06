# Cherry Blossom Phenology Analysis

This repository contains data and analysis scripts for modeling the changing time of first bloom and full bloom for cherry blossoms in Japan.

## Project Structure

- `data/`: Contains the historic dataset from Yasuyuki Aono (Kyoto full bloom dates from 812 AD).
- `docs/`: Notes and instructions for the project.
- `plots/`: Generated plots for the Aono dataset (x2 vs t, dx2/dt vs x2).
- `scripts/`: Python scripts for data processing and plotting.

## How to run

```bash
# To generate plots for the Aono dataset:
python scripts/plot_aono.py
```
