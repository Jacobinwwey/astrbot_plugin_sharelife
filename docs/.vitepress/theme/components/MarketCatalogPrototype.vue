<script setup lang="ts">
import { withBase } from 'vitepress'
import { computed, onMounted, ref } from 'vue'

const props = defineProps<{
  locale?: 'zh' | 'en' | 'ja'
}>()

type Row = {
  pack_id: string
  template_id?: string
  title?: string
  description?: string
  version: string
  pack_type: 'bot_profile_pack' | 'extension_pack'
  risk_level: 'low' | 'medium' | 'high'
  compatibility: 'compatible' | 'degraded' | 'blocked'
  review_labels: string[]
  warning_flags: string[]
  source_channel: string
  maintainer: string
  package_path: string
  featured?: boolean
  engagement?: {
    installs?: number
    trial_requests?: number
  }
  sections?: string[]
}

type RiskLevel = 'low' | 'medium' | 'high'
type PackType = 'bot_profile_pack' | 'extension_pack'

const fallbackRows: Row[] = [
  {
    pack_id: 'profile/official-starter',
    template_id: 'profile/official-starter',
    title: 'Official Starter',
    description: 'Starter baseline profile-pack for first import, compare, and apply walkthrough.',
    version: '1.0.1',
    pack_type: 'bot_profile_pack',
    risk_level: 'low',
    compatibility: 'compatible',
    review_labels: ['approved', 'official_profile_pack', 'risk_low'],
    warning_flags: [],
    source_channel: 'bundled_official',
    maintainer: 'Sharelife',
    package_path: '/market/packages/official/profile-official-starter-1-0-1.zip',
    featured: true,
    engagement: { installs: 248, trial_requests: 61 },
    sections: ['astrbot_core', 'providers', 'plugins'],
  },
  {
    pack_id: 'profile/official-safe-reference',
    template_id: 'profile/official-safe-reference',
    title: 'Official Safe Reference',
    description: 'Safety-first reference profile-pack for strict apply, rollback, and audit review.',
    version: '1.0.1',
    pack_type: 'bot_profile_pack',
    risk_level: 'low',
    compatibility: 'compatible',
    review_labels: ['approved', 'official_profile_pack', 'risk_low'],
    warning_flags: [],
    source_channel: 'bundled_official',
    maintainer: 'Sharelife',
    package_path: '/market/packages/official/profile-official-safe-reference-1-0-1.zip',
    featured: true,
    engagement: { installs: 179, trial_requests: 47 },
    sections: ['astrbot_core', 'providers', 'plugins'],
  },
]

const rows = ref<Row[]>(fallbackRows)

function normalizeSnapshotRows(input: unknown): Row[] {
  if (!Array.isArray(input)) return []
  const out: Row[] = []
  input.forEach((item) => {
    if (!item || typeof item !== 'object') return
    const row = item as Partial<Row>
    const packId = String(row.pack_id || row.template_id || '').trim()
    const version = String(row.version || '').trim()
    const packagePath = String(row.package_path || '').trim()
    if (!packId || !version || !packagePath) return
    out.push({
      pack_id: packId,
      template_id: packId,
      title: String(row.title || packId).trim(),
      description: String(row.description || '').trim(),
      version,
      pack_type: (String(row.pack_type || 'bot_profile_pack') as PackType) || 'bot_profile_pack',
      risk_level: (String(row.risk_level || 'low') as RiskLevel) || 'low',
      compatibility: (String(row.compatibility || 'compatible') as Row['compatibility']) || 'compatible',
      review_labels: Array.isArray(row.review_labels)
        ? row.review_labels.map((entry) => String(entry || '').trim()).filter(Boolean)
        : [],
      warning_flags: Array.isArray(row.warning_flags)
        ? row.warning_flags.map((entry) => String(entry || '').trim()).filter(Boolean)
        : [],
      source_channel: String(row.source_channel || 'community_submission'),
      maintainer: String(row.maintainer || 'community'),
      package_path: packagePath,
      featured: Boolean(row.featured),
      engagement: {
        installs: Number((row.engagement && row.engagement.installs) || 0),
        trial_requests: Number((row.engagement && row.engagement.trial_requests) || 0),
      },
      sections: Array.isArray(row.sections)
        ? row.sections.map((entry) => String(entry || '').trim()).filter(Boolean)
        : [],
    })
  })
  return out
}

onMounted(async () => {
  try {
    const response = await fetch(withBase('/market/catalog.snapshot.json'), {
      method: 'GET',
      cache: 'no-store',
    })
    if (!response.ok) {
      return
    }
    const payload = await response.json()
    const loadedRows = normalizeSnapshotRows((payload && payload.rows) || [])
    if (loadedRows.length > 0) {
      rows.value = loadedRows
    }
  } catch (_error) {
    // fallback rows keep docs page functional when snapshot is unavailable.
  }
})

const query = ref('')
const risk = ref('')
const packType = ref('')

const labels = {
  zh: {
    search: '搜索 profile-pack',
    searchPlaceholder: '按 pack id、标题或标签搜索',
    risk: '风险级别',
    packType: '包类型',
    allRisk: '全部风险',
    allPackType: '全部类型',
    empty: '无匹配结果',
    download: '下载包',
    sectionCount: 'Sections',
    installs: '安装',
    trials: '试用',
    tableHeaders: {
      pack: 'Profile-Pack',
      version: '版本',
      risk: '风险',
      type: '类型',
      labels: '标签',
      compatibility: '兼容性',
      source: '来源',
      maintainer: '维护者',
      package: '下载',
    },
    riskLabels: { low: '低', medium: '中', high: '高' },
    packTypeLabels: {
      bot_profile_pack: 'Bot Profile Pack',
      extension_pack: 'Extension Pack',
    },
    sourceLabels: {
      bundled_official: '官方内置',
      community_submission: '社区投稿',
    },
    compatibilityLabels: {
      compatible: '兼容',
      degraded: '降级',
      blocked: '阻断',
    },
    tagLabels: {
      approved: '已批准',
      official_profile_pack: '官方参考',
      risk_low: '低风险',
    },
  },
  en: {
    search: 'Search profile packs',
    searchPlaceholder: 'Search by pack id, title, or labels',
    risk: 'Risk level',
    packType: 'Pack type',
    allRisk: 'All risks',
    allPackType: 'All pack types',
    empty: 'No matched records',
    download: 'Download',
    sectionCount: 'Sections',
    installs: 'Installs',
    trials: 'Trials',
    tableHeaders: {
      pack: 'Profile Pack',
      version: 'Version',
      risk: 'Risk',
      type: 'Type',
      labels: 'Labels',
      compatibility: 'Compatibility',
      source: 'Source',
      maintainer: 'Maintainer',
      package: 'Package',
    },
    riskLabels: { low: 'Low', medium: 'Medium', high: 'High' },
    packTypeLabels: {
      bot_profile_pack: 'Bot Profile Pack',
      extension_pack: 'Extension Pack',
    },
    sourceLabels: {
      bundled_official: 'Bundled official',
      community_submission: 'Community submission',
    },
    compatibilityLabels: {
      compatible: 'Compatible',
      degraded: 'Degraded',
      blocked: 'Blocked',
    },
    tagLabels: {
      approved: 'Approved',
      official_profile_pack: 'Official reference',
      risk_low: 'Low risk',
    },
  },
  ja: {
    search: 'profile-pack を検索',
    searchPlaceholder: 'pack id、タイトル、ラベルで検索',
    risk: 'リスク',
    packType: 'パック種別',
    allRisk: 'すべて',
    allPackType: 'すべて',
    empty: '一致するデータがありません',
    download: 'ダウンロード',
    sectionCount: 'Sections',
    installs: '導入',
    trials: '試用',
    tableHeaders: {
      pack: 'Profile-Pack',
      version: 'バージョン',
      risk: 'リスク',
      type: '種別',
      labels: 'ラベル',
      compatibility: '互換性',
      source: 'ソース',
      maintainer: 'メンテナー',
      package: 'ダウンロード',
    },
    riskLabels: { low: '低', medium: '中', high: '高' },
    packTypeLabels: {
      bot_profile_pack: 'Bot Profile Pack',
      extension_pack: 'Extension Pack',
    },
    sourceLabels: {
      bundled_official: '公式同梱',
      community_submission: 'コミュニティ投稿',
    },
    compatibilityLabels: {
      compatible: '互換',
      degraded: '一部制限',
      blocked: 'ブロック',
    },
    tagLabels: {
      approved: '承認済み',
      official_profile_pack: '公式リファレンス',
      risk_low: '低リスク',
    },
  },
} as const

const locale = computed(() => props.locale ?? 'en')
const text = computed(() => labels[locale.value])
const riskOptions: RiskLevel[] = ['low', 'medium', 'high']
const packTypes: PackType[] = ['bot_profile_pack', 'extension_pack']
const tableHeaderOrder = ['pack', 'version', 'risk', 'type', 'labels', 'compatibility', 'source', 'maintainer', 'package'] as const
const tableHeaders = computed(() => tableHeaderOrder.map((item) => text.value.tableHeaders[item]))

const displayRisk = (value: string) => text.value.riskLabels[(value as RiskLevel) || 'low'] || value
const displayPackType = (value: string) => text.value.packTypeLabels[(value as PackType) || 'bot_profile_pack'] || value
const displaySource = (value: string) => text.value.sourceLabels[value as keyof typeof text.value.sourceLabels] || value
const displayCompatibility = (value: string) =>
  text.value.compatibilityLabels[(value as Row['compatibility']) || 'compatible'] || value
const displayTag = (value: string) => text.value.tagLabels[value as keyof typeof text.value.tagLabels] || value

const localizedLabels = (item: Row) =>
  [...item.review_labels, ...item.warning_flags]
    .map((entry) => displayTag(entry))
    .join(', ')

const localizedSearchText = (item: Row) =>
  [
    item.pack_id,
    item.title || '',
    item.description || '',
    item.review_labels.join(' '),
    item.warning_flags.join(' '),
    item.sections?.join(' ') || '',
    displayPackType(item.pack_type),
    displaySource(item.source_channel),
  ]
    .join(' ')
    .toLowerCase()

const filteredRows = computed(() => {
  const q = query.value.trim().toLowerCase()
  const selectedRisk = risk.value.trim().toLowerCase()
  const selectedType = packType.value.trim().toLowerCase()
  return rows.value.filter((item) => {
    if (q && !localizedSearchText(item).includes(q)) {
      return false
    }
    if (selectedRisk && item.risk_level !== selectedRisk) {
      return false
    }
    if (selectedType && item.pack_type !== selectedType) {
      return false
    }
    return true
  })
})

const packageUrl = (path: string) => withBase(path)
</script>

<template>
  <div class="market-prototype">
    <div class="filters">
      <label>
        {{ text.search }}
        <input v-model="query" type="text" :placeholder="text.searchPlaceholder" />
      </label>
      <label>
        {{ text.risk }}
        <select v-model="risk">
          <option value="">{{ text.allRisk }}</option>
          <option v-for="item in riskOptions" :key="item" :value="item">{{ displayRisk(item) }}</option>
        </select>
      </label>
      <label>
        {{ text.packType }}
        <select v-model="packType">
          <option value="">{{ text.allPackType }}</option>
          <option v-for="item in packTypes" :key="item" :value="item">{{ displayPackType(item) }}</option>
        </select>
      </label>
    </div>

    <table class="catalog-table" v-if="filteredRows.length > 0">
      <thead>
        <tr>
          <th v-for="item in tableHeaders" :key="item">{{ item }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in filteredRows" :key="`${item.pack_id}@${item.version}`">
          <td>
            <div class="pack-cell">
              <strong>{{ item.title || item.pack_id }}</strong>
              <small>{{ item.pack_id }}</small>
              <span v-if="item.description">{{ item.description }}</span>
            </div>
          </td>
          <td>{{ item.version }}</td>
          <td>{{ displayRisk(item.risk_level) }}</td>
          <td>{{ displayPackType(item.pack_type) }}</td>
          <td>{{ localizedLabels(item) || `${text.sectionCount}: ${item.sections?.length || 0}` }}</td>
          <td>{{ displayCompatibility(item.compatibility) }}</td>
          <td>{{ displaySource(item.source_channel) }}</td>
          <td>{{ item.maintainer }}</td>
          <td>
            <a :href="packageUrl(item.package_path)" target="_blank" rel="noreferrer">
              {{ text.download }}
            </a>
            <small class="download-meta">
              {{ text.installs }} {{ item.engagement?.installs || 0 }} · {{ text.trials }} {{ item.engagement?.trial_requests || 0 }}
            </small>
          </td>
        </tr>
      </tbody>
    </table>
    <p v-else class="empty">{{ text.empty }}</p>
  </div>
</template>

<style scoped>
.market-prototype {
  display: grid;
  gap: 0.9rem;
}

.filters {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 0.75rem;
}

.filters label {
  display: grid;
  gap: 0.32rem;
  font-size: 0.85rem;
}

.filters input,
.filters select {
  border: 1px solid var(--vp-c-divider);
  border-radius: 8px;
  padding: 0.45rem 0.6rem;
}

.catalog-table {
  width: 100%;
  border-collapse: collapse;
}

.catalog-table th,
.catalog-table td {
  border: 1px solid var(--vp-c-divider);
  padding: 0.6rem;
  text-align: left;
  font-size: 0.85rem;
  vertical-align: top;
}

.pack-cell {
  display: grid;
  gap: 0.2rem;
}

.pack-cell small,
.download-meta {
  color: var(--vp-c-text-2);
}

.pack-cell span {
  color: var(--vp-c-text-2);
}

.download-meta {
  display: block;
  margin-top: 0.25rem;
}

.empty {
  color: var(--vp-c-text-2);
}
</style>
