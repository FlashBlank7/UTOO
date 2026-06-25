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
  { id: 'sunday', weekday: 0, label: '周日', image: sunday, theme: '银杏和风' },
  { id: 'monday', weekday: 1, label: '周一', image: monday, theme: '研究室蓝牌' },
  { id: 'tuesday', weekday: 2, label: '周二', image: tuesday, theme: '蓝黄校园针织' },
  { id: 'wednesday', weekday: 3, label: '周三', image: wednesday, theme: '银杏通勤' },
  { id: 'thursday', weekday: 4, label: '周四', image: thursday, theme: '技术研究室' },
  { id: 'friday', weekday: 5, label: '周五', image: friday, theme: '赤门咖啡' },
  { id: 'saturday', weekday: 6, label: '周六', image: saturday, theme: '校园社群' }
]

export const neutralMascotImage = neutral
