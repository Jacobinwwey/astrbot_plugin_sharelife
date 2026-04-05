import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'
import MarketCatalogPrototype from './components/MarketCatalogPrototype.vue'

const theme: Theme = {
  ...DefaultTheme,
  enhanceApp({ app }) {
    DefaultTheme.enhanceApp?.({ app })
    app.component('MarketCatalogPrototype', MarketCatalogPrototype)
  },
}

export default theme
