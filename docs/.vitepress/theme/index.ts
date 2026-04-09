import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import MarketCatalogPrototype from './components/MarketCatalogPrototype.vue'
import MarketCenterProgressBoard from './components/MarketCenterProgressBoard.vue'

const theme: Theme = {
  ...DefaultTheme,
  enhanceApp({ app }) {
    DefaultTheme.enhanceApp?.({ app })
    app.component('MarketCatalogPrototype', MarketCatalogPrototype)
    app.component('MarketCenterProgressBoard', MarketCenterProgressBoard)
  },
}

export default theme
