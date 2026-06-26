export type StickerTextPart =
  | { type: 'text'; text: string }
  | { type: 'sticker'; code: string; label: string; src: string }

export type YutokoSticker = {
  code: string
  label: string
  src: string
}

export const yutokoStickers: YutokoSticker[] = [
  { code: ':yutoko_thanks:', label: '谢谢', src: '/stickers/yutoko/thanks.png' },
  { code: ':yutoko_bye:', label: '再见', src: '/stickers/yutoko/bye.png' },
  { code: ':yutoko_cheer:', label: '应援！', src: '/stickers/yutoko/cheer.png' },
  { code: ':yutoko_not_school:', label: '不登校！', src: '/stickers/yutoko/not-school.png' },
  { code: ':yutoko_yubikubi:', label: '優比丘比～', src: '/stickers/yutoko/yubikubi.png' },
  { code: ':yutoko_roger:', label: '收到！', src: '/stickers/yutoko/roger.png' },
  { code: ':yutoko_otsukare:', label: '辛苦了！', src: '/stickers/yutoko/otsukare.png' },
  { code: ':yutoko_pat:', label: '摸摸头', src: '/stickers/yutoko/pat.png' }
]

const stickerByCode = new Map(yutokoStickers.map((sticker) => [sticker.code, sticker]))
const stickerPattern = new RegExp(
  yutokoStickers.map((sticker) => sticker.code.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|'),
  'g'
)

export function parseStickerText(text: string): StickerTextPart[] {
  if (!text) return []
  const parts: StickerTextPart[] = []
  let lastIndex = 0

  for (const match of text.matchAll(stickerPattern)) {
    const code = match[0]
    const index = match.index ?? 0
    const sticker = stickerByCode.get(code)
    if (!sticker) continue

    if (index > lastIndex) {
      parts.push({ type: 'text', text: text.slice(lastIndex, index) })
    }
    parts.push({ type: 'sticker', ...sticker })
    lastIndex = index + code.length
  }

  if (lastIndex < text.length) {
    parts.push({ type: 'text', text: text.slice(lastIndex) })
  }

  return parts
}

export function stickerPlainText(text: string): string {
  return text.replace(stickerPattern, (code) => {
    const sticker = stickerByCode.get(code)
    return sticker ? `[Yutoko: ${sticker.label}]` : code
  })
}
