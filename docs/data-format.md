# `ini_xyr.dat` data format

`ini_xyr.dat` is the particle-coordinate input consumed by ZDEM_DFN. The
parser is intentionally small and follows the format already used by the
original engine.

## Particle records

A particle record is a non-empty line with at least three whitespace-separated
fields whose first three fields can be parsed as floating-point numbers:

```text
x y r
```

- `x`: particle center X coordinate
- `y`: particle center Y coordinate
- `r`: particle radius

The program uses these values as supplied. Coordinate and radius units are
defined by the upstream ZDEM model convention; ZDEM_DFN performs **no unit
conversion**.

Additional fields are accepted during parsing but are ignored. This makes
files with an existing trailing tag readable. When ZDEM_DFN writes tagged
output, the tag is appended after a tab, for example:

```text
2.200000000000e+03  3.200000000000e+03  1.200000000000e+02\tDFN_Matrix
```

## Other line types

- Blank lines are preserved as blank lines.
- Non-blank lines whose first three fields are not all numeric are preserved as
  header/metadata lines.
- There is no required header syntax. Comment lines beginning with `#` are a
  convenient convention and are preserved verbatim.
- A file with no valid particle records is rejected by the CLI.

## Minimum valid file

```text
# Synthetic demo data (not laboratory measurements)
2.200000000000e+03  3.200000000000e+03  1.200000000000e+02
```

The bundled `examples/demo_case/ini_xyr.dat` is a short, fully synthetic
fixture for installation and pipeline checks. It is not a measured specimen
and must not be used as experimental evidence.

## Directory layout

Single-case input:

```text
case/
└── ini_xyr.dat
```

Run it with the recommended safe interface:

```bash
python -m zdem_dfn \
  --input case \
  --output outputs/case \
  --seed 42
```

The output directory is created automatically and contains:

```text
outputs/case/
├── ini_xyr_dfn.dat
└── dfn_preview.png
```

The original `case/ini_xyr.dat` is not modified. In compatibility `--dirs`
mode, tagged files are written beside each source by default and the preview
path is controlled by `--out`. Use `--in-place` only with
the legacy interface when deliberately choosing to overwrite the source file. `--dry-run` checks the input and prints the planned paths without
creating the output directory or any artifact.

## Multiple conditions

The compatibility interface accepts multiple case directories:

```bash
python -m zdem_dfn --dirs case_a case_b --out outputs/preview.png --seed 42
```

Each source directory receives its tagged file next to its input by default.
Use `--suffix` to change the tagged filename, or `--in-place` to explicitly
restore the legacy overwrite behavior. The `--input/--output` interface is
intentionally limited to one case so its output directory remains unambiguous.

## Reports

`--stats PATH` writes network statistics (`.csv` selects CSV; other suffixes
select Markdown). `--rose PATH` writes a fracture-strike rose diagram. Both
are regular output artifacts and are skipped, like all other writes, during
`--dry-run`.
