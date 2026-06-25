import monday from './week/monday.png'
import tuesday from './week/tuesday.png'
import wednesday from './week/wednesday.png'
import thursday from './week/thursday.png'
import friday from './week/friday.png'
import saturday from './week/saturday.png'
import sunday from './week/sunday.png'
import neutral from './avatar-neutral.png'

export type MascotOutfit = {
  id: string
  weekday: number
  label: string
  image: string
  theme: string
}

export const mascotOutfits: MascotOutfit[] = [
  { id: 'sunday', weekday: 0, label: '周日', image: sunday, theme: '和风休息日' },
  { id: 'monday', weekday: 1, label: '周一', image: monday, theme: '学术实验室' },
  { id: 'tuesday', weekday: 2, label: '周二', image: tuesday, theme: '校园 hoodie' },
  { id: 'wednesday', weekday: 3, label: '周三', image: wednesday, theme: '清爽制服' },
  { id: 'thursday', weekday: 4, label: '周四', image: thursday, theme: '技术外套' },
  { id: 'friday', weekday: 5, label: '周五', image: friday, theme: '咖啡围裙' },
  { id: 'saturday', weekday: 6, label: '周六', image: saturday, theme: '街头休闲' }
]

export const neutralMascotImage = neutral
