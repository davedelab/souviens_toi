# Souviens-toi
Capture & organise notes, web clips, PDF, images.  

## Encoding helper

If you ever observe `UnicodeDecodeError`s when launching the app (accented literals saved with Windows encoding), run:

```
python scripts/fix_encoding.py [targets...]
```

By default this script scans `memex_next/` and re-saves `.py` files as UTF-8 with UNIX line endings. Use `--dry-run` to preview the files it would change and `--encoding cp1252` to fallback to another source encoding if needed.

