# Table: Group-Weight Sensitivity

| setting | weights | obj diff | boundary diff | patch diff | different cells | note |
|---|---|---:|---:|---:|---:|---|
| baseline | `(1.0, 0.8, 0.5)` | -0.57 | 1750 | 2 | 4 | default |
| transit_heavier | `(1.0, 1.0, 0.5)` | -0.56 | 1750 | 2 | 4 | alternate robustness check |
| soft_heavier | `(1.0, 0.8, 0.8)` | -0.58 | 1750 | 2 | 4 | stable |
| fixed_lighter | `(0.8, 0.8, 0.5)` | -0.57 | 1750 | 2 | 4 | stable |
| compressed_weights | `(1.0, 0.9, 0.7)` | -0.57 | 1750 | 2 | 4 | preferred robustness check |
