<script setup lang="ts">
import { computed, ref } from 'vue'
import { withBase } from 'vitepress'

type Locale = 'zh' | 'en' | 'ja'
type VariantKey = 'variant_1' | 'variant_2' | 'variant_3' | 'variant_4' | 'variant_5'

const props = defineProps<{
  locale?: Locale
}>()

const locale = computed<Locale>(() => props.locale ?? 'en')
const activeVariantKey = ref<VariantKey>('variant_3')

const baseImage = (filename: string) => withBase(`/private/market-center-progress/${filename}`)

const variantMeta = {
  variant_1: {
    screenId: '0a22321fc4244a8cbb4b80c7ff88543a',
    htmlUrl:
      'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzlkMjU2MDI4ZmI2ZjRhYjVhMmU2MWMyODNkYzVkMjg3EgsSBxDD6PDTnAMYAZIBIwoKcHJvamVjdF9pZBIVQhMxNzkxOTQxNjM0ODIzNDA3NDYx&filename=&opi=96797242',
    screenshot: baseImage('variant_1.png'),
  },
  variant_2: {
    screenId: '926623465dd94241a9f2f4ba68811dad',
    htmlUrl:
      'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzlmNmYzNmYxMGFhNzQ2OTBhMTBjMWVlY2VjOWZkMWM0EgsSBxDD6PDTnAMYAZIBIwoKcHJvamVjdF9pZBIVQhMxNzkxOTQxNjM0ODIzNDA3NDYx&filename=&opi=96797242',
    screenshot: baseImage('variant_2.png'),
  },
  variant_3: {
    screenId: '4d71151e5e0a499fbbb9e2b78b7676aa',
    htmlUrl:
      'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzQ2ZTc2MGJjOWYzMTQ0NzRhNzBkYzVmNWRiNzI0OTFkEgsSBxDD6PDTnAMYAZIBIwoKcHJvamVjdF9pZBIVQhMxNzkxOTQxNjM0ODIzNDA3NDYx&filename=&opi=96797242',
    screenshot: baseImage('variant_3.png'),
  },
  variant_4: {
    screenId: '2faed839bb5d4de4ad6887c795b30733',
    htmlUrl:
      'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sX2Y0N2EwNWE5YjEyNTQxNGE5NTNlMmEyZGExNDUyOWE2EgsSBxDD6PDTnAMYAZIBIwoKcHJvamVjdF9pZBIVQhMxNzkxOTQxNjM0ODIzNDA3NDYx&filename=&opi=96797242',
    screenshot: baseImage('variant_4.png'),
  },
  variant_5: {
    screenId: '9ad760cf710c4b83972b04fbe2e39580',
    htmlUrl:
      'https://contribution.usercontent.google.com/download?c=CgthaWRhX2NvZGVmeBJ7Eh1hcHBfY29tcGFuaW9uX2dlbmVyYXRlZF9maWxlcxpaCiVodG1sXzc5ZTM3MTBkMGFkZTQyYWQ4MWVhOThjZjc4OTA2MTc0EgsSBxDD6PDTnAMYAZIBIwoKcHJvamVjdF9pZBIVQhMxNzkxOTQxNjM0ODIzNDA3NDYx&filename=&opi=96797242',
    screenshot: baseImage('variant_5.png'),
  },
} as const

const copy = {
  en: {
    heroEyebrow: '54068 progress surface',
    heroTitle: 'Market center baseline and derived detail plan',
    heroBody:
      'This board keeps the current public-first market center as the only visual source-of-truth, then compares the current native detail shell against the aligned Stitch variants already recorded in `sharelife/webui/market_detail/Design.md`.',
    chips: ['Public-first entry locked', 'Variant 3 is the active native baseline', 'Selective sync stays inside install intent'],
    metaHeading: 'Recorded Stitch lineage',
    metaProject: 'Project',
    metaBaseline: 'Baseline screen',
    metaSession: 'Variant session',
    metaNative: 'Native direction',
    metaNativeValue: 'Variant 3 split facts vs actions',
    baselineHeading: 'Baseline comparison',
    cards: {
      market: {
        title: 'Current market center baseline',
        body: 'Public browsing, Spotlight-style search, and result controls remain on the page. No member action is allowed before card entry.',
        points: [
          'Search stays under the entry header.',
          'Sort and results stay below search.',
          'Cards remain public and read-only.',
        ],
      },
      native: {
        title: 'Current native detail stack',
        body: 'The local implementation already hosts five switchable detail compositions inside the real market shell.',
        points: [
          'Same pack context survives variant switching.',
          'Protected actions remain in the native action rail.',
          'The shell already reflects current runtime constraints.',
        ],
      },
      derived: {
        title: 'Approved derived baseline',
        body: 'Variant 3 remains the preferred bridge between the market page and the detail layer because it preserves public facts first and member action readiness second.',
        points: [
          'Left: facts, trust, and declared sections.',
          'Right: action readiness and selective sync framing.',
          'Install-time stateful sync stays explicit.',
        ],
      },
      member: {
        title: 'User-side baseline that must stay separate',
        body: 'The member panel still owns workspace-scale flows and should not be flattened into the market detail drawer.',
        points: [
          'Export, import, import + dry-run',
          'Apply, rollback, plugin-install advanced paths',
          'Shared contracts, different surface ownership',
        ],
      },
    },
    variantsHeading: 'Aligned Stitch variants',
    variantsBody:
      'Each variant below was regenerated against the current market-center baseline and can be opened directly from the same selected pack context. Variant 3 remains the primary native implementation target.',
    focusLabel: 'Focus',
    screenLabel: 'Screen',
    activeLabel: 'Active native baseline',
    openHtml: 'Open Stitch HTML',
    openImage: 'Open local screenshot',
    matrixHeading: 'Shared contract matrix',
    matrixColumns: ['Area', 'Member-side baseline', 'Market detail baseline', 'Next convergence move'],
    matrixRows: [
      {
        area: 'Install options',
        member: '`preflight`, `force_reinstall`, `source_preference`, `selected_sections`',
        market: 'Same contract, but only revealed after card entry and before protected install starts.',
        next: 'Extract one normalization helper and keep the detail-only action boundary.',
      },
      {
        area: 'Upload options',
        member: '`scan_mode`, `visibility`, `replace_existing`',
        market: 'Shown from detail-bound member flows, not from the public grid.',
        next: 'Keep one payload contract, but preserve market vs workspace responsibilities.',
      },
      {
        area: 'Profile-pack submit',
        member: '`submit_options.pack_type`, `submit_options.selected_sections`, `submit_options.redaction_mode`',
        market: 'Same downstream API normalization, framed around the selected card context.',
        next: 'Unify option shaping, not the full screen layout.',
      },
      {
        area: 'Stateful sync',
        member: 'Optional during import/apply review.',
        market: '`memory_store`, `conversation_history`, and `knowledge_base` stay explicit inside install intent.',
        next: 'Continue the explicit deselect-before-install model in Variant 3 and downstream variants.',
      },
    ],
    pathHeading: 'Next path',
    pathSteps: [
      'Keep the current market entry unchanged and continue detail-only iteration.',
      'Refine Variant 3 spacing, copy hierarchy, and selective-sync affordances first.',
      'Backfill Variants 1, 2, 4, and 5 as V3-derived native compositions rather than detached placeholders.',
      'Converge the smallest shared helper for install and submit option normalization across member and market surfaces.',
      'Before any new Stitch call, update `sharelife/webui/market_detail/Design.md`, then follow the documented wait-five-minutes fetch sequence.',
    ],
    variantLabels: {
      variant_1: 'Variant 1',
      variant_2: 'Variant 2',
      variant_3: 'Variant 3',
      variant_4: 'Variant 4',
      variant_5: 'Variant 5',
    },
    variantTitles: {
      variant_1: 'Editorial evidence-first',
      variant_2: 'Dense operator console',
      variant_3: 'Split facts vs actions',
      variant_4: 'Trust and risk first',
      variant_5: 'Checklist-first execution',
    },
    variantFocus: {
      variant_1: 'Narrative framing, evidence grouping, review reading flow',
      variant_2: 'Compact control density and operator scanning speed',
      variant_3: 'Stable bridge from public facts to protected member actions',
      variant_4: 'Risk gates, compatibility posture, trust framing',
      variant_5: 'Step order, auth timing, install checklist clarity',
    },
    variantNotes: {
      variant_1: [
        'Best when the user needs review context before acting.',
        'Maintains current shell tone without becoming a marketing page.',
        'Useful as a documentation-heavy comparison mode.',
      ],
      variant_2: [
        'Most compact and utilitarian of the five variants.',
        'Good for operators who already know the pack and need quick checks.',
        'Needs careful density tuning to avoid visual drift from the market baseline.',
      ],
      variant_3: [
        'Best overall alignment with the approved market-center baseline.',
        'Public facts remain primary while actions stay ready but secondary.',
        'Selective sync remains legible without turning into a detached wizard.',
      ],
      variant_4: [
        'Useful when risk and compatibility signals should dominate first read.',
        'Good fit for suspicious or degraded packs.',
        'Should remain a mode inside the same shell, not a separate alert screen.',
      ],
      variant_5: [
        'Most procedural of the five variants.',
        'Clarifies auth timing and install prerequisites for less familiar members.',
        'Works best as a guided execution mode after facts have been inspected.',
      ],
    },
  },
  zh: {
    heroEyebrow: '54068 进度面板',
    heroTitle: '市场中心基线与派生细则层方案',
    heroBody:
      '这个面板把当前 public-first 市场中心作为唯一视觉真值，然后对照当前原生细则层实现与已记录在 `sharelife/webui/market_detail/Design.md` 中的对齐后 Stitch 变体。',
    chips: ['市场首屏基线已锁定', '方案 3 是当前原生主基线', 'Selective sync 保持在 install intent 内'],
    metaHeading: '已记录的 Stitch 血缘',
    metaProject: '项目',
    metaBaseline: '基线 screen',
    metaSession: 'Variant session',
    metaNative: '原生推进方向',
    metaNativeValue: '方案 3：公开事实 / 成员动作分栏',
    baselineHeading: '基线对比',
    cards: {
      market: {
        title: '当前市场中心基线',
        body: '公开浏览、Spotlight 式搜索和结果控制继续留在页面层。用户在点卡入层前不能直接执行成员动作。',
        points: ['搜索框位于入口头部下方。', '排序与结果控制位于搜索框下方。', '卡片保持公开、只读、可浏览。'],
      },
      native: {
        title: '当前原生细则层栈',
        body: '本地实现已经在真实市场壳层里承载五个可切换细则层构图。',
        points: ['切换 variant 时同一 pack 上下文不丢失。', '受保护动作仍保留在原生 action rail。', '当前壳层已经反映真实运行时约束。'],
      },
      derived: {
        title: '已批准的派生基线',
        body: '方案 3 仍然是市场页与细则层之间最合适的桥梁，因为它坚持 public facts first、member action readiness second。',
        points: ['左侧：事实、信任、已声明 sections。', '右侧：动作就绪与 selective sync 提示。', '安装时的 stateful sync 仍然显式可见。'],
      },
      member: {
        title: '必须保持独立的用户侧基线',
        body: '成员面板仍然负责工作区级流程，不应被压扁进市场细则层抽屉。',
        points: ['导出、导入、导入 + dry-run', 'apply、rollback、plugin-install 高级路径', '共享 contract，但 surface ownership 不同'],
      },
    },
    variantsHeading: '对齐后的 Stitch 变体',
    variantsBody:
      '下面五个变体都已经基于当前市场中心基线重生成，并可在同一选中 pack 上下文里一键切换查看。方案 3 仍然是当前原生实现的第一优先。',
    focusLabel: '聚焦点',
    screenLabel: 'Screen',
    activeLabel: '当前原生主基线',
    openHtml: '打开 Stitch HTML',
    openImage: '打开本地截图',
    matrixHeading: '共享契约矩阵',
    matrixColumns: ['领域', '用户侧基线', '市场细则层基线', '下一步收敛动作'],
    matrixRows: [
      {
        area: '安装选项',
        member: '`preflight`、`force_reinstall`、`source_preference`、`selected_sections`',
        market: '同一 contract，但只在点卡入层后、真正执行 install 前展示。',
        next: '抽出一个归一化 helper，同时保持 detail-only 的动作边界。',
      },
      {
        area: '上传选项',
        member: '`scan_mode`、`visibility`、`replace_existing`',
        market: '从细则层内的成员动作触发，不出现在公开卡片网格里。',
        next: '统一 payload contract，但保留市场与工作区的职责分工。',
      },
      {
        area: 'Profile-pack 提交',
        member: '`submit_options.pack_type`、`submit_options.selected_sections`、`submit_options.redaction_mode`',
        market: '下游 API 归一化一致，但界面要围绕选中卡片上下文表达。',
        next: '统一选项整形，不强行统一整个屏幕布局。',
      },
      {
        area: '有状态同步',
        member: '在 import / apply 审阅时可选。',
        market: '`memory_store`、`conversation_history`、`knowledge_base` 在 install intent 内保持显式。',
        next: '继续保持“安装前可取消选择”的模型，并优先深化方案 3。',
      },
    ],
    pathHeading: '下一步路径',
    pathSteps: [
      '保持市场首屏不变，后续只在细则层继续迭代。',
      '优先深化方案 3 的间距、信息层级和 selective-sync 提示方式。',
      '把方案 1、2、4、5 继续补成 V3 派生的原生构图，而不是脱节占位稿。',
      '在成员侧与市场侧之间收敛最小共享 helper，用于 install 和 submit 选项归一化。',
      '下一次调用 Stitch 之前，先更新 `sharelife/webui/market_detail/Design.md`，再按文档要求等待五分钟后抓取结果。',
    ],
    variantLabels: {
      variant_1: '方案 1',
      variant_2: '方案 2',
      variant_3: '方案 3',
      variant_4: '方案 4',
      variant_5: '方案 5',
    },
    variantTitles: {
      variant_1: '叙事化证据优先',
      variant_2: '高密度操作台',
      variant_3: '公开事实 / 成员动作分栏',
      variant_4: '信任与风险优先',
      variant_5: '执行清单优先',
    },
    variantFocus: {
      variant_1: '叙事导向、证据分组、审阅阅读流',
      variant_2: '压缩式控制密度与操作员扫描效率',
      variant_3: '从公开事实平滑过渡到受保护成员动作',
      variant_4: '风险门槛、兼容性态势、信任表达',
      variant_5: '步骤顺序、鉴权时机、安装清单清晰度',
    },
    variantNotes: {
      variant_1: [
        '适合用户在行动前先阅读审阅上下文。',
        '保持当前壳层气质，不会滑向营销页。',
        '适合作为文档感更强的对比模式。',
      ],
      variant_2: [
        '五个变体里最紧凑、最偏操作台。',
        '适合已经熟悉 pack、只需要快速扫描的用户。',
        '需要谨慎控制密度，避免偏离当前市场基线。',
      ],
      variant_3: [
        '与已批准市场中心基线的整体对齐度最高。',
        '公开事实仍是主位，动作处于就绪但次位。',
        'Selective sync 清晰可读，但不会变成独立向导。',
      ],
      variant_4: [
        '适合让风险与兼容性在第一眼更强地主导阅读。',
        '更适合可疑或 degraded 的 pack。',
        '仍应作为同一壳层内的模式，而不是独立告警页。',
      ],
      variant_5: [
        '五个变体里最强调流程顺序。',
        '适合帮助不熟悉的成员理解鉴权与安装前提。',
        '更适合在事实确认之后作为执行引导模式。',
      ],
    },
  },
  ja: {
    heroEyebrow: '54068 進捗サーフェス',
    heroTitle: 'Market Center baseline と派生 detail plan',
    heroBody:
      'このボードは current public-first market center を唯一の visual source-of-truth とし、その上で current native detail shell と `sharelife/webui/market_detail/Design.md` に記録済みの aligned Stitch variants を比較します。',
    chips: ['market first-screen baseline は固定', 'Variant 3 が current native baseline', 'selective sync は install intent 内に維持'],
    metaHeading: '記録済み Stitch lineage',
    metaProject: 'Project',
    metaBaseline: 'Baseline screen',
    metaSession: 'Variant session',
    metaNative: 'Native 実装方針',
    metaNativeValue: 'Variant 3 facts/actions split',
    baselineHeading: 'Baseline 比較',
    cards: {
      market: {
        title: '現在の market center baseline',
        body: '公開 browse、Spotlight 風 search、result controls は page 側に残ります。card entry 前に member action は実行されません。',
        points: ['search は entry header の下に置く。', 'sort と result controls は search の下に置く。', 'cards は public / read-only browse のまま保つ。'],
      },
      native: {
        title: '現在の native detail stack',
        body: 'local implementation は real market shell の中で 5 つの switchable detail composition をすでに保持しています。',
        points: ['variant を切り替えても pack context は維持される。', 'protected actions は native action rail に残る。', 'runtime constraints を反映した shell がすでにある。'],
      },
      derived: {
        title: '承認済みの派生 baseline',
        body: 'Variant 3 は public facts first と member action readiness second を保つため、market page と detail layer の橋として最も妥当です。',
        points: ['左: facts、trust、宣言済み sections', '右: action readiness と selective sync framing', 'install 時の stateful sync が明示的に見える'],
      },
      member: {
        title: '分離を維持すべき user-side baseline',
        body: 'member panel は workspace 規模の flow を持ち続けるべきで、market detail drawer に押し込むべきではありません。',
        points: ['export、import、import + dry-run', 'apply、rollback、plugin-install advanced path', 'shared contract、different surface ownership'],
      },
    },
    variantsHeading: 'aligned Stitch variants',
    variantsBody:
      '以下の 5 variant は current market-center baseline に合わせて再生成済みで、同じ selected pack context のまま one-click で比較できます。Variant 3 が current native implementation の第一優先です。',
    focusLabel: 'Focus',
    screenLabel: 'Screen',
    activeLabel: 'Current native baseline',
    openHtml: 'Stitch HTML を開く',
    openImage: 'ローカル screenshot を開く',
    matrixHeading: 'Shared contract matrix',
    matrixColumns: ['領域', 'member-side baseline', 'market detail baseline', '次の収束アクション'],
    matrixRows: [
      {
        area: 'Install options',
        member: '`preflight`、`force_reinstall`、`source_preference`、`selected_sections`',
        market: '同じ contract だが、card entry 後かつ protected install 開始前にだけ見せる。',
        next: '1 つの normalization helper を抽出しつつ、detail-only action boundary を維持する。',
      },
      {
        area: 'Upload options',
        member: '`scan_mode`、`visibility`、`replace_existing`',
        market: 'public grid ではなく detail-bound member flow から見せる。',
        next: 'payload contract は共有し、market と workspace の責務分割は残す。',
      },
      {
        area: 'Profile-pack submit',
        member: '`submit_options.pack_type`、`submit_options.selected_sections`、`submit_options.redaction_mode`',
        market: 'downstream API normalization は同じだが、selected card context に結びつけて見せる。',
        next: 'option shaping は収束させるが、screen shape 全体は無理に統一しない。',
      },
      {
        area: 'Stateful sync',
        member: 'import / apply review 時に optional。',
        market: '`memory_store`、`conversation_history`、`knowledge_base` を install intent 内で明示する。',
        next: 'install 前 deselect モデルを維持し、Variant 3 でさらに磨く。',
      },
    ],
    pathHeading: '次の道筋',
    pathSteps: [
      'market first screen はそのまま維持し、detail layer のみ継続改善する。',
      'まず Variant 3 の余白、コピー階層、selective-sync affordance を深める。',
      'Variants 1, 2, 4, 5 も V3 派生の native composition として埋め、切り離された placeholder にしない。',
      'member と market の間で install / submit option normalization の最小 shared helper を収束させる。',
      '次の Stitch call 前に `sharelife/webui/market_detail/Design.md` を更新し、文書化済みの 5 分待機シーケンスを守る。',
    ],
    variantLabels: {
      variant_1: 'Variant 1',
      variant_2: 'Variant 2',
      variant_3: 'Variant 3',
      variant_4: 'Variant 4',
      variant_5: 'Variant 5',
    },
    variantTitles: {
      variant_1: 'Editorial evidence-first',
      variant_2: 'Dense operator console',
      variant_3: 'Split facts vs actions',
      variant_4: 'Trust and risk first',
      variant_5: 'Checklist-first execution',
    },
    variantFocus: {
      variant_1: 'narrative framing、evidence grouping、review reading flow',
      variant_2: 'compact control density と operator scan speed',
      variant_3: 'public facts から protected member action への安定した橋',
      variant_4: 'risk gate、compatibility posture、trust framing',
      variant_5: 'step order、auth timing、install checklist clarity',
    },
    variantNotes: {
      variant_1: [
        '行動前に review context を読みたい時に向く。',
        'current shell tone を保ち、marketing page 化しない。',
        'documentation-heavy な比較モードとして使いやすい。',
      ],
      variant_2: [
        '5 variants の中で最も compact で utilitarian。',
        'pack をよく知る operator が quick check したい時に向く。',
        'current market baseline から drift しないよう density tuning が必要。',
      ],
      variant_3: [
        '承認済み market-center baseline との整合が最も高い。',
        'public facts が主で、actions は ready だが従。',
        'selective sync が読み取りやすく、独立 wizard 化しない。',
      ],
      variant_4: [
        'risk と compatibility を first read で強く見せたい場合に向く。',
        '疑わしい pack や degraded pack に合う。',
        '同じ shell 内のモードとして扱い、別製品の alert screen にしない。',
      ],
      variant_5: [
        '5 variants の中で最も procedural。',
        'auth timing と install prerequisite を unfamiliar member に説明しやすい。',
        'facts 確認後の guided execution mode として最適。',
      ],
    },
  },
} as const

const text = computed(() => copy[locale.value])

const variantOrder: VariantKey[] = ['variant_1', 'variant_2', 'variant_3', 'variant_4', 'variant_5']

const variants = computed(() =>
  variantOrder.map((key) => ({
    key,
    screenId: variantMeta[key].screenId,
    htmlUrl: variantMeta[key].htmlUrl,
    screenshot: variantMeta[key].screenshot,
    label: text.value.variantLabels[key],
    title: text.value.variantTitles[key],
    focus: text.value.variantFocus[key],
    notes: text.value.variantNotes[key],
  }))
)

const activeVariant = computed(
  () => variants.value.find((item) => item.key === activeVariantKey.value) ?? variants.value[2]
)

const projectId = 'projects/1791941634823407461'
const baselineScreenId = '3ef1d2a12c3449f593141520a70ec987'
const variantSessionId = '14727920063696137864'
</script>

<template>
  <div class="market-progress-shell">
    <section class="market-progress-hero">
      <div class="market-progress-copy">
        <div class="market-progress-eyebrow">{{ text.heroEyebrow }}</div>
        <h2>{{ text.heroTitle }}</h2>
        <p>{{ text.heroBody }}</p>
        <div class="market-progress-chip-row">
          <span v-for="chip in text.chips" :key="chip" class="market-progress-chip">{{ chip }}</span>
        </div>
      </div>
      <aside class="market-progress-meta">
        <div class="market-progress-panel-title">{{ text.metaHeading }}</div>
        <dl>
          <div>
            <dt>{{ text.metaProject }}</dt>
            <dd>{{ projectId }}</dd>
          </div>
          <div>
            <dt>{{ text.metaBaseline }}</dt>
            <dd>{{ baselineScreenId }}</dd>
          </div>
          <div>
            <dt>{{ text.metaSession }}</dt>
            <dd>{{ variantSessionId }}</dd>
          </div>
          <div>
            <dt>{{ text.metaNative }}</dt>
            <dd>{{ text.metaNativeValue }}</dd>
          </div>
        </dl>
      </aside>
    </section>

    <section class="market-progress-section">
      <div class="market-progress-section-head">
        <h3>{{ text.baselineHeading }}</h3>
      </div>
      <div class="market-progress-baseline-grid">
        <article class="market-progress-card">
          <div class="market-progress-card-media is-cropped-top">
            <img :src="baseImage('market-center-baseline.png')" :alt="text.cards.market.title" />
          </div>
          <div class="market-progress-card-body">
            <h4>{{ text.cards.market.title }}</h4>
            <p>{{ text.cards.market.body }}</p>
            <ul>
              <li v-for="point in text.cards.market.points" :key="point">{{ point }}</li>
            </ul>
          </div>
        </article>

        <article class="market-progress-card">
          <div class="market-progress-card-media">
            <img :src="baseImage('native-detail-stack.png')" :alt="text.cards.native.title" />
          </div>
          <div class="market-progress-card-body">
            <h4>{{ text.cards.native.title }}</h4>
            <p>{{ text.cards.native.body }}</p>
            <ul>
              <li v-for="point in text.cards.native.points" :key="point">{{ point }}</li>
            </ul>
          </div>
        </article>

        <article class="market-progress-card">
          <div class="market-progress-card-media">
            <img :src="variantMeta.variant_3.screenshot" :alt="text.cards.derived.title" />
          </div>
          <div class="market-progress-card-body">
            <h4>{{ text.cards.derived.title }}</h4>
            <p>{{ text.cards.derived.body }}</p>
            <ul>
              <li v-for="point in text.cards.derived.points" :key="point">{{ point }}</li>
            </ul>
          </div>
        </article>

        <article class="market-progress-card market-progress-card-note">
          <div class="market-progress-card-body">
            <h4>{{ text.cards.member.title }}</h4>
            <p>{{ text.cards.member.body }}</p>
            <ul>
              <li v-for="point in text.cards.member.points" :key="point">{{ point }}</li>
            </ul>
          </div>
        </article>
      </div>
    </section>

    <section class="market-progress-section">
      <div class="market-progress-section-head">
        <h3>{{ text.variantsHeading }}</h3>
        <p>{{ text.variantsBody }}</p>
      </div>

      <div class="market-progress-tab-row" role="tablist" :aria-label="text.variantsHeading">
        <button
          v-for="variant in variants"
          :key="variant.key"
          class="market-progress-tab"
          :class="{ 'is-active': variant.key === activeVariant.key }"
          type="button"
          role="tab"
          :aria-selected="variant.key === activeVariant.key ? 'true' : 'false'"
          @click="activeVariantKey = variant.key"
        >
          <span>{{ variant.label }}</span>
        </button>
      </div>

      <div class="market-progress-variant-grid">
        <figure class="market-progress-variant-preview">
          <img :src="activeVariant.screenshot" :alt="activeVariant.title" />
        </figure>
        <article class="market-progress-variant-detail">
          <div class="market-progress-variant-active">{{ text.activeLabel }}</div>
          <h4>{{ activeVariant.title }}</h4>
          <div class="market-progress-variant-focus">
            <span>{{ text.focusLabel }}</span>
            <strong>{{ activeVariant.focus }}</strong>
          </div>
          <div class="market-progress-variant-screen">
            <span>{{ text.screenLabel }}</span>
            <strong>{{ activeVariant.screenId }}</strong>
          </div>
          <ul>
            <li v-for="note in activeVariant.notes" :key="note">{{ note }}</li>
          </ul>
          <div class="market-progress-link-row">
            <a :href="activeVariant.htmlUrl" target="_blank" rel="noreferrer">{{ text.openHtml }}</a>
            <a :href="activeVariant.screenshot" target="_blank" rel="noreferrer">{{ text.openImage }}</a>
          </div>
        </article>
      </div>
    </section>

    <section class="market-progress-section">
      <div class="market-progress-section-head">
        <h3>{{ text.matrixHeading }}</h3>
      </div>
      <div class="market-progress-table-wrap">
        <table class="market-progress-table">
          <thead>
            <tr>
              <th v-for="header in text.matrixColumns" :key="header">{{ header }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in text.matrixRows" :key="row.area">
              <th>{{ row.area }}</th>
              <td>{{ row.member }}</td>
              <td>{{ row.market }}</td>
              <td>{{ row.next }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="market-progress-section">
      <div class="market-progress-section-head">
        <h3>{{ text.pathHeading }}</h3>
      </div>
      <ol class="market-progress-path">
        <li v-for="step in text.pathSteps" :key="step">{{ step }}</li>
      </ol>
    </section>
  </div>
</template>

<style scoped>
.market-progress-shell {
  --progress-border: rgba(24, 24, 27, 0.12);
  --progress-panel: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(245, 246, 248, 0.92));
  --progress-ink: #111318;
  --progress-muted: #55606f;
  --progress-accent: #111111;
  display: grid;
  gap: 1.5rem;
  margin: 1.25rem 0 2rem;
}

.dark .market-progress-shell {
  --progress-border: rgba(244, 244, 245, 0.16);
  --progress-panel: linear-gradient(180deg, rgba(24, 24, 27, 0.9), rgba(15, 23, 42, 0.88));
  --progress-ink: #f5f6f8;
  --progress-muted: #b6c0cc;
  --progress-accent: #fafafa;
}

.market-progress-hero,
.market-progress-card,
.market-progress-variant-grid,
.market-progress-table-wrap,
.market-progress-section {
  border: 1px solid var(--progress-border);
  border-radius: 24px;
  background: var(--progress-panel);
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.08);
}

.market-progress-hero {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1.6fr) minmax(280px, 0.9fr);
  padding: 1.5rem;
}

.market-progress-copy h2,
.market-progress-section-head h3,
.market-progress-card-body h4,
.market-progress-variant-detail h4 {
  margin: 0;
  color: var(--progress-ink);
}

.market-progress-eyebrow,
.market-progress-panel-title,
.market-progress-variant-active {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--progress-muted);
}

.market-progress-copy p,
.market-progress-section-head p,
.market-progress-card-body p,
.market-progress-variant-detail ul,
.market-progress-path,
.market-progress-table td,
.market-progress-table th {
  color: var(--progress-muted);
}

.market-progress-chip-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
  margin-top: 1rem;
}

.market-progress-chip {
  border-radius: 999px;
  border: 1px solid var(--progress-border);
  padding: 0.4rem 0.7rem;
  font-size: 0.82rem;
  color: var(--progress-ink);
  background: rgba(255, 255, 255, 0.66);
}

.dark .market-progress-chip {
  background: rgba(39, 39, 42, 0.72);
}

.market-progress-meta {
  border-radius: 20px;
  border: 1px solid var(--progress-border);
  background: rgba(255, 255, 255, 0.52);
  padding: 1rem;
}

.dark .market-progress-meta {
  background: rgba(24, 24, 27, 0.48);
}

.market-progress-meta dl {
  margin: 0.9rem 0 0;
  display: grid;
  gap: 0.85rem;
}

.market-progress-meta dt {
  font-size: 0.8rem;
  color: var(--progress-muted);
}

.market-progress-meta dd {
  margin: 0.2rem 0 0;
  font-size: 0.94rem;
  color: var(--progress-ink);
  word-break: break-word;
}

.market-progress-section {
  padding: 1.3rem;
}

.market-progress-section-head {
  display: grid;
  gap: 0.45rem;
  margin-bottom: 1rem;
}

.market-progress-baseline-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.market-progress-card {
  overflow: hidden;
}

.market-progress-card-media {
  background: linear-gradient(180deg, rgba(229, 231, 235, 0.86), rgba(244, 244, 245, 0.72));
  padding: 0.7rem;
}

.dark .market-progress-card-media {
  background: linear-gradient(180deg, rgba(39, 39, 42, 0.82), rgba(17, 24, 39, 0.7));
}

.market-progress-card-media img,
.market-progress-variant-preview img {
  display: block;
  width: 100%;
  border-radius: 16px;
  border: 1px solid var(--progress-border);
  background: #fff;
}

.market-progress-card-media.is-cropped-top img {
  height: 300px;
  object-fit: cover;
  object-position: top center;
}

.market-progress-card-body {
  display: grid;
  gap: 0.7rem;
  padding: 1rem 1rem 1.15rem;
}

.market-progress-card-body ul,
.market-progress-variant-detail ul {
  margin: 0;
  padding-left: 1.1rem;
  display: grid;
  gap: 0.4rem;
}

.market-progress-tab-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  margin-bottom: 1rem;
}

.market-progress-tab {
  border: 1px solid var(--progress-border);
  border-radius: 999px;
  padding: 0.55rem 0.9rem;
  background: rgba(255, 255, 255, 0.7);
  color: var(--progress-muted);
  cursor: pointer;
  transition: transform 120ms ease, border-color 120ms ease, background 120ms ease;
}

.market-progress-tab:hover {
  transform: translateY(-1px);
  border-color: rgba(17, 17, 17, 0.26);
}

.market-progress-tab.is-active {
  background: var(--progress-accent);
  color: #ffffff;
  border-color: var(--progress-accent);
}

.dark .market-progress-tab {
  background: rgba(24, 24, 27, 0.72);
}

.market-progress-variant-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: minmax(0, 1.3fr) minmax(300px, 0.9fr);
  padding: 1rem;
}

.market-progress-variant-preview {
  margin: 0;
}

.market-progress-variant-detail {
  display: grid;
  gap: 0.85rem;
  align-content: start;
}

.market-progress-variant-focus,
.market-progress-variant-screen {
  display: grid;
  gap: 0.25rem;
}

.market-progress-variant-focus span,
.market-progress-variant-screen span {
  font-size: 0.8rem;
  color: var(--progress-muted);
}

.market-progress-variant-focus strong,
.market-progress-variant-screen strong {
  color: var(--progress-ink);
}

.market-progress-link-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.market-progress-link-row a {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--progress-border);
  border-radius: 999px;
  padding: 0.6rem 0.9rem;
  text-decoration: none;
  color: var(--progress-ink);
  background: rgba(255, 255, 255, 0.68);
}

.dark .market-progress-link-row a {
  background: rgba(24, 24, 27, 0.7);
}

.market-progress-table-wrap {
  overflow-x: auto;
}

.market-progress-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 780px;
}

.market-progress-table thead th {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.market-progress-table th,
.market-progress-table td {
  padding: 0.95rem 0.9rem;
  border-bottom: 1px solid var(--progress-border);
  vertical-align: top;
  text-align: left;
}

.market-progress-table tbody th {
  color: var(--progress-ink);
  font-size: 0.92rem;
}

.market-progress-path {
  margin: 0;
  padding-left: 1.2rem;
  display: grid;
  gap: 0.55rem;
}

@media (max-width: 960px) {
  .market-progress-hero,
  .market-progress-variant-grid,
  .market-progress-baseline-grid {
    grid-template-columns: 1fr;
  }

  .market-progress-card-media.is-cropped-top img {
    height: auto;
    object-fit: contain;
  }
}
</style>
