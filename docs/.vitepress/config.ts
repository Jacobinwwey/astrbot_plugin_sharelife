import { defineConfig } from 'vitepress'

const base = process.env.DOCS_BASE || '/astrbot_plugin_sharelife/'

export default defineConfig({
  title: 'Sharelife Docs',
  description: 'Sharelife architecture, governance, and operations documentation',
  base,
  lastUpdated: true,
  cleanUrls: true,
  locales: {
    root: {
      label: '简体中文',
      lang: 'zh-CN',
      link: '/zh/',
      title: 'Sharelife 文档',
      description: 'Sharelife 架构、治理与运维文档'
    },
    en: {
      label: 'English',
      lang: 'en-US',
      link: '/en/',
      title: 'Sharelife Docs',
      description: 'Sharelife architecture, governance and operations docs'
    },
    ja: {
      label: '日本語 (Beta)',
      lang: 'ja-JP',
      link: '/ja/',
      title: 'Sharelife ドキュメント',
      description: 'Sharelife の設計・運用ドキュメント'
    }
  },
  themeConfig: {
    search: {
      provider: 'local'
    },
    nav: [
      { text: '中文', link: '/zh/' },
      { text: 'English', link: '/en/' },
      { text: '日本語', link: '/ja/' }
    ],
    sidebar: {
      '/zh/': [
        {
          text: 'User Guide (用户指南)',
          items: [
            { text: '3 分钟快速跑通', link: '/zh/tutorials/3-minute-quickstart' },
            { text: '快速开始', link: '/zh/tutorials/get-started' },
            { text: '初始化向导与配置模板', link: '/zh/how-to/init-wizard-and-config-template' },
            { text: 'Bot Profile Pack 操作', link: '/zh/how-to/bot-profile-pack' },
            { text: '独立 WebUI 使用', link: '/zh/how-to/webui-page' },
            { text: 'GitHub Pages 发布', link: '/zh/how-to/github-pages-publish' },
            { text: '市场只读公开页', link: '/zh/how-to/market-public-hub' },
            { text: '市场目录原型页', link: '/zh/how-to/market-catalog-prototype' },
            { text: '为什么社区优先', link: '/zh/explanation/community-first' }
          ]
        },
        {
          text: 'Developers (架构与开发)',
          items: [
            { text: '权限边界与职责解耦路线图', link: '/zh/reference/permission-boundary-roadmap' },
            { text: '用户面板与市场页重构执行方案', link: '/zh/reference/user-panel-stitch-execution-plan' },
            { text: '存储持久化与冷备执行方案', link: '/zh/reference/storage-cold-backup-execution-plan' },
            { text: '集成执行手册（UI x 存储）', link: '/zh/reference/integrated-execution-playbook' },
            { text: 'Sharelife v1 Freeze', link: '/zh/reference/sharelife-v1-freeze' },
            { text: 'API v1', link: '/zh/reference/api-v1' },
            { text: 'Bot 配置迁移范围（真值表）', link: '/zh/how-to/profile-pack-migration-scope' },
            { text: '插件生态 Round 2 基线', link: '/zh/how-to/plugin-ecosystem-round2-baseline' },
            { text: '插件生态 Round 3 架构', link: '/zh/how-to/plugin-ecosystem-round3-stability-plan' }
          ]
        }
      ],
      '/en/': [
        {
          text: 'User Guide',
          items: [
            { text: '3-Minute QuickStart', link: '/en/tutorials/3-minute-quickstart' },
            { text: 'Get Started', link: '/en/tutorials/get-started' },
            { text: 'Init Wizard + Config Template', link: '/en/how-to/init-wizard-and-config-template' },
            { text: 'Bot Profile Pack Operations', link: '/en/how-to/bot-profile-pack' },
            { text: 'Standalone WebUI', link: '/en/how-to/webui-page' },
            { text: 'GitHub Pages Publish', link: '/en/how-to/github-pages-publish' },
            { text: 'Public Market Read-Only Hub', link: '/en/how-to/market-public-hub' },
            { text: 'Market Catalog Prototype', link: '/en/how-to/market-catalog-prototype' },
            { text: 'Why Community-First', link: '/en/explanation/community-first' }
          ]
        },
        {
          text: 'Developers',
          items: [
            { text: 'Permission Boundary Roadmap', link: '/en/reference/permission-boundary-roadmap' },
            { text: 'User Panel + Market Refactor Plan', link: '/en/reference/user-panel-stitch-execution-plan' },
            { text: 'Storage Cold Backup Plan', link: '/en/reference/storage-cold-backup-execution-plan' },
            { text: 'Integrated Execution Playbook', link: '/en/reference/integrated-execution-playbook' },
            { text: 'Sharelife v1 Freeze', link: '/en/reference/sharelife-v1-freeze' },
            { text: 'API v1', link: '/en/reference/api-v1' },
            { text: 'Bot Profile Migration Scope', link: '/en/how-to/profile-pack-migration-scope' },
            { text: 'Plugin Ecosystem Round 2 Baseline', link: '/en/how-to/plugin-ecosystem-round2-baseline' },
            { text: 'Plugin Ecosystem Round 3 Stability Plan', link: '/en/how-to/plugin-ecosystem-round3-stability-plan' }
          ]
        }
      ],
      '/ja/': [
        {
          text: 'User Guide (ユーザーガイド)',
          items: [
            { text: '3分クイックスタート', link: '/ja/tutorials/3-minute-quickstart' },
            { text: 'クイックスタート', link: '/ja/tutorials/get-started' },
            { text: '初期化ウィザードと設定テンプレート', link: '/ja/how-to/init-wizard-and-config-template' },
            { text: 'Bot Profile Pack 運用', link: '/ja/how-to/bot-profile-pack' },
            { text: 'スタンドアロン WebUI', link: '/ja/how-to/webui-page' },
            { text: 'GitHub Pages 公開', link: '/ja/how-to/github-pages-publish' },
            { text: '公開マーケット（読み取り専用）', link: '/ja/how-to/market-public-hub' },
            { text: 'マーケットカタログ試作ページ', link: '/ja/how-to/market-catalog-prototype' },
            { text: 'コミュニティ優先の理由', link: '/ja/explanation/community-first' }
          ]
        },
        {
          text: 'Developers (開発とアーキテクチャ)',
          items: [
            { text: '権限制御境界ロードマップ', link: '/ja/reference/permission-boundary-roadmap' },
            { text: 'ユーザーパネル + マーケット再設計 実行計画', link: '/ja/reference/user-panel-stitch-execution-plan' },
            { text: 'ストレージ永続化 + 冷備 実行計画', link: '/ja/reference/storage-cold-backup-execution-plan' },
            { text: '統合実行プレイブック', link: '/ja/reference/integrated-execution-playbook' },
            { text: 'API v1', link: '/ja/reference/api-v1' },
            { text: 'Bot 設定移行スコープ', link: '/ja/how-to/profile-pack-migration-scope' },
            { text: 'プラグインエコシステム Round 2 基線', link: '/ja/how-to/plugin-ecosystem-round2-baseline' },
            { text: 'プラグインエコシステム Round 3 安定性計画', link: '/ja/how-to/plugin-ecosystem-round3-stability-plan' }
          ]
        }
      ]
    }
  }
})
