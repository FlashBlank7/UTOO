# Yutoko / 優都子 Sticker Pack v1

This note records the first public forum sticker pack for `Yutoko / 優都子 / ゆとこ`.

## Output paths

Public sticker PNGs:

- `frontend/public/stickers/yutoko/thanks.png` -> `:yutoko_thanks:` -> `谢谢`
- `frontend/public/stickers/yutoko/bye.png` -> `:yutoko_bye:` -> `再见`
- `frontend/public/stickers/yutoko/cheer.png` -> `:yutoko_cheer:` -> `应援！`
- `frontend/public/stickers/yutoko/not-school.png` -> `:yutoko_not_school:` -> `不登校！`
- `frontend/public/stickers/yutoko/yubikubi.png` -> `:yutoko_yubikubi:` -> `優比丘比～`
- `frontend/public/stickers/yutoko/roger.png` -> `:yutoko_roger:` -> `收到！`
- `frontend/public/stickers/yutoko/otsukare.png` -> `:yutoko_otsukare:` -> `辛苦了！`
- `frontend/public/stickers/yutoko/pat.png` -> `:yutoko_pat:` -> `摸摸头`

## Visual direction

- True one-head-body chibi sticker style. Do not crop a full-body mascot export into a head sticker.
- Adult-coded Yutoko, cute and lightly erokawaii while staying all-ages safe.
- Black bob hair, cat ears, cat tail, visible ginkgo detail, UTokyo Blue `#0B8BEE`, Yellow `#FFCD00`, and an original UTOO double-ginkgo badge feeling.
- No official University of Tokyo logo, logotype, symbol mark, emblem, or readable official university text.
- No nudity, exposed intimate body parts, transparent underwear, explicit sexual motion, or underage-coded sexualization.

## Generation prompt pattern

Each source image used the same structure, with the action changed per sticker:

```text
Create a true one-head-body chibi sticker illustration of Yutoko / 優都子, the original UTOO mascot, on a perfectly flat solid #00ff00 chroma-key background for background removal.

Yutoko is an adult-coded cute catgirl mascot with black bob hair, black cat ears, black tail, a visible ginkgo hairpin, UTokyo Blue and Yellow accents, and an original UTOO double-ginkgo badge feeling. The style must be a real chibi sticker drawing: very large head, tiny body, simplified limbs, compact silhouette, expressive pose, thick clean outline, glossy anime sticker rendering, no full-body standing illustration crop.

Use the requested emotion/action. Do not draw any text in the image; text will be added locally for accuracy.
Keep the subject fully separated from the background with crisp edges and generous padding.
Do not use #00ff00 anywhere in the subject. No shadow, no watermark.
```

The final exact captions were added locally with a CJK system font so `優比丘比～` remains correct.
