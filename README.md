# social-assets

Public CDN for Spark Careers social-post visuals. Buffer fetches PNGs from
`raw.githubusercontent.com` URLs of this repo.

## Layout

```
YYYY/Wnn/                   weekly visuals (ISO week)
  2026-W22-mon-b2b.png      naming convention: {iso-week}-{weekday}-{audience}.png
  2026-W22-mon-b2c.png
  ...
tools/
  finalize_buffer_csvs.py   substitutes __REPLACE_*__ placeholders in Buffer CSVs
                            with raw.githubusercontent.com URLs
```

## Weekly workflow

1. Drop new PNGs into `YYYY/Wnn/`.
2. `git add . && git commit -m "wNN: visuals" && git push`.
3. `python tools/finalize_buffer_csvs.py --week 2026-W22 \
       --input <bundle>/buffer --output <bundle>/buffer`
4. Bulk-upload the three `*-final.csv` files to Buffer (one per channel).
