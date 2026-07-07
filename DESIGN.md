# Design

> greenroom 控制台的视觉系统。token 与 telos 共享单源（`telos/docs/tokens.css`）——改核心 token 两端同步；`--ok/--warn/--live` 是 greenroom 面试场景的语义扩展。
> 标 **方向** 的是本轮（暖白底子 + 更大胆编辑表达）要往的目标，未必是当前代码现状。

## 2026-07-05 调研校准：landing 与 product 分层

这次校准不再把首页视觉和工作台视觉混用。参考源：
- Linear UI redesign: 减少视觉噪音、保持对齐、提升导航层级和密度。https://linear.app/now/how-we-redesigned-the-linear-ui
- Vercel Geist: Geist Sans / Mono 面向开发者和设计师，强调 simplicity、minimalism、speed、precision、clarity、functionality。https://vercel.com/font
- Vercel Geist Design System: 高对比、网格、组件一致性。https://vercel.com/geist/introduction
- IBM Carbon for AI: AI 样式只用于标识 AI 出现、透明度和解释性，不做装饰。https://carbondesignsystem.com/guidelines/carbon-for-ai/
- Google PAIR Guidebook: AI 产品先定义用户需要、心理模型、反馈/控制、可解释性和失败处理。https://pair.withgoogle.com/guidebook/
- Figma UI principles: hierarchy、progressive disclosure、consistency、contrast、accessibility、proximity、alignment。https://www.figma.com/resource-library/ui-design-principles/

落地规则：
- **Landing page**：允许品牌表达、Fraunces/wordmark、宽松留白、叙事型模块。目标是解释定位和建立记忆点。
- **Product app**：默认是高频工具，不做大 hero。标题用 Geist/Inter 系 UI 字体，字号克制；页面层级靠 app shell、导航、列表密度、控件状态和内容优先级建立。
- **AI-native**：AI 不等于发光卡片和“智能感”装饰。只在生成中、解释来源、可撤回/可调整、系统不确定时显性表达；其它时候 AI 隐入任务流。
- **组件库**：当前是 vanilla 单文件，所以组件库表现为内部 primitives，而不是引入 React 组件包：button、field、segmented、chip、list-row、panel、sheet、toast、prose、empty state。每个 primitive 必须有 default / hover / focus / active / disabled / loading / error 的设计位。
- **字体分工修正**：Geist Sans = 产品 UI 主字体；Geist Mono = 元数据、命令、计数；Fraunces = landing、品牌、长文档/报告里的编辑声，不再作为工作台通用 h1。

## 2026-07-05 组件级硬约束

这轮不再按“单屏好看”推进，而按产品系统推进。对标原则：
- Geist Typography 把 heading / button / label / copy 分成不同阶梯；greenroom 产品态也必须区分标题、标签、正文和计数，不能用一个大标题体系铺全站。https://vercel.com/geist/typography
- Linear 2026 refresh 的核心是“不要让未获得注意力的元素抢注意力”“结构要被感到而不是被看见”；greenroom 的 nav、filter、side panel 只能承担定位，不抢主任务内容。https://linear.app/now/behind-the-latest-design-refresh
- Linear 2024 redesign 的方法是按 sidebar / tabs / headers / panels / lists 等基础件做 stress test；greenroom 后续每次改动必须先问属于哪种 view pattern。https://linear.app/now/how-we-redesigned-the-linear-ui
- Carbon AI Label 明确 AI 标识不是装饰，也不是触发 AI 动作的按钮；greenroom 只在生成、来源、可解释和失败边界处标 AI。https://carbondesignsystem.com/components/ai-label/usage/
- Google PAIR 的基线是用户心理模型、控制、反馈和失败处理；greenroom 不能只展示“AI 生成”，必须展示它生成到哪里、可怎么撤回/继续。https://pair.withgoogle.com/guidebook/

落地到代码：
- `body.in-app` 是产品壳层：Geist Sans、14px 基准、56px 顶栏、紧凑 nav、弱边框、减少投影。
- `body.landing-mode` 是市场页：允许 wordmark、大叙事、Fraunces、宽留白。
- `list-head` 是所有列表页头唯一 primitive；资料、经历库、岗位百科都走它，避免突然进入一堆 chip。
- `kfilters` 是查询栏，不是页面标题；移动端横向滚动，桌面端 sticky。
- `su-side` 是行动/生成闭环，不是重复说明卡；桌面解释流程，移动端压成底部行动条。
- 禁用、按压、focus-visible 是组件基础态，不允许只做 hover。

## 2026-07-05 二次调研落地：世界级 AI-native 的判断标准

这次不再用“像某个参考图”判断，而拆成可复用标准：

1. **产品 chrome 后退。** Linear 2026 refresh 的重点是：未获得注意力的导航、边框、图标要退，主任务内容前进；结构要被感到，不要被看见。greenroom 产品态必须减少黑色大胶囊、厚边框、重复报头和大卡片，把注意力让给“当前候选岗位/当前材料/当前提词”。
   来源：https://linear.app/now/behind-the-latest-design-refresh
2. **字体不是装饰，是信息密度。** Vercel Geist 的价值是 clarity/functionality，适合高频工具；Fraunces 只留给 landing、品牌和长文档的编辑声。工作台里大衬线标题会立刻滑向 AI 模板感。
   来源：https://vercel.com/font 和 https://vercel.com/geist/typography
3. **AI-native 不是“AI 风格”。** Carbon AI label 的原则是识别、透明度和解释性；PAIR 的原则是用户心理模型、反馈、控制和失败处理。greenroom 里 AI 只能在“正在生成/基于哪些材料/如何撤回或继续/哪里失败”出现，不做发光边框和智能感装饰。
   来源：https://carbondesignsystem.com/components/ai-label/usage/ 与 https://pair.withgoogle.com/guidebook/
4. **反 AI 味要有明确禁令。** 2026 年已经出现可识别的 AI 设计套话：奶油底、大衬线、锈橙点缀、tracked-out 小标题、多层圆角卡片/描边。greenroom 可以保留暖纸，但必须用冷静的信息架构、真实任务状态、少量深绿/黄铜语义色把它从模板里拉出来。
   参考观察：https://www.newyorker.com/culture/infinite-scroll/the-ai-design-aesthetic-thats-taking-over-the-internet

产品态新增硬标准：
- **字体阶梯**：页面标题 21-24px / section 14-16px / 正文 13.5-14px / label 10.5-11px；不随 viewport 放大；letter-spacing 默认 0，只有 mono label 可小幅正字距。
- **控件阶梯**：topbar 52-56px；button 高 30-36px；segmented 不用黑色大胶囊，默认浅底、选中白底或 stage tint；primary action 才用深绿。
- **页面模式**：列表页用 `list-head + row/list`；配置页用 `form stream + sticky action rail`；详情页用 `compact title + tabs + reading rail`；landing 才允许叙事模块和品牌戏剧性。
- **卡片预算**：一个视口内最多 1 个强卡片/面板；其余用发丝线、留白、浅底。卡片不能嵌套卡片。
- **移动端**：底部 tab 只承担导航；主要行动如果是生成/开始类，使用 sticky action rail；内容块不再白卡堆叠。

## 2026-07-05 三次调研：字体、组件库、界面规范的硬基线

这轮把“世界级 AI-native”拆成可审计基线，不再只做局部美化：

- **字体系统参考 Apple HIG + Geist。** Apple HIG 要求文本和图标在所有字号下保持可读，布局要适配字体变化；Geist 的 typography 把 heading、copy、label、button、mono 元数据分成清晰阶梯。greenroom 产品态统一使用 Geist Sans 做 UI，Geist Mono 只做命令/计数/时间/状态；Fraunces 只留给 landing、品牌和长文档，不再进入工作台常规标题。
  来源：https://developer.apple.com/design/human-interface-guidelines/typography 与 https://vercel.com/geist/typography
- **组件库参考 Radix/Linear 的“行为与样式分离”。** Radix Primitives 的核心价值是 accessibility 和可组合 primitives；Linear 案例说明 checkbox、switch、radio、dialog 等基础件应从产品里抽出可复用行为，再由品牌层定义视觉。greenroom 目前是单文件 vanilla，不引入 React 组件库，但内部必须按 `button / field / segmented / tabs / list-row / panel / sheet / dialog / palette / bottom-nav` 管控，不能每屏自造一套。
  来源：https://www.radix-ui.com/primitives/case-studies/linear
- **AI 组件参考 Carbon AI Label。** AI 标识只用于透明度、识别和解释性，不能当“生成按钮”或装饰符。greenroom 的 AI-native 表达必须落在生成边界、来源边界、失败边界、可撤回/继续边界；其它界面用常规产品组件完成。
  来源：https://carbondesignsystem.com/components/ai-label/usage/
- **信息架构参考 Linear refresh。** 导航、tabs、headers、panels 统一降低噪声、增强对齐和密度；未获得注意力的元素不抢主任务焦点。greenroom 所有产品页都遵守：顶部只定位，页面头只说明当前任务，主内容直接进入材料/问题/提词/岗位，不重复展示“页面名 + 大标题 + 同义说明”。
  来源：https://linear.app/now/behind-the-latest-design-refresh
- **AI-native 工作流参考 Claude Design 的设计系统输入思想。** AI 辅助设计不是让界面呈现“AI 味”，而是把品牌、字体、组件和代码库规范作为输入持续应用。greenroom 的后续迭代默认先更新设计规范，再改界面。
  来源：https://www.anthropic.com/news/claude-design-anthropic-labs

组件验收表：
- **Button**：高度 30/34/38 三档；primary 只用于提交/开始/生成；secondary 是浅底线框；icon button 必须有稳定尺寸。
- **Field**：label 11px mono/sans、输入 14px、圆角 9-10px、focus 用 `--ring`；错误和离线提示占同一信息位。
- **Segmented**：浅底、白色选中、深绿只用于强行动，不用于 tab 选中。
- **Panel/Card**：默认无投影或极弱投影；可点对象才有 hover；阅读内容用线和留白，不用连续白卡。
- **Dialog/Palette**：半径 12-14px，搜索输入和列表行密度接近 Linear/Command menu，不用大圆角玻璃卡。
- **Bottom nav**：移动端底部导航只表达位置；不能像主 CTA；当前态用小面积 stage tint。

## 2026-07-05 四次调研：从参考到验收项

用户明确指出“字体、组件库、设计规范不能只是说说”。因此后续每一轮不按截图好坏主观判断，而按这些验收项检查：

- **字体验收**：产品 UI 中，常规标题、按钮、表单、正文必须回到 Geist Sans 的固定字号阶；Fraunces 只用于 landing、品牌和长文档。Apple HIG 的重点是可读性、信息层级和适配，不能用大衬线标题掩盖结构问题。来源：https://developer.apple.com/design/human-interface-guidelines/typography
- **组件验收**：单文件实现也必须像组件库一样管理 primitives。Radix 的价值是把 accessibility、行为和组合性沉到基础组件；greenroom 对应到 button、field、segmented、tabs、list-row、sheet、dialog、palette、bottom-nav 的统一状态。来源：https://www.radix-ui.com/primitives/case-studies/linear
- **密度验收**：Vercel Geist/Linear 的共同点是高密度但清晰，控件只承载操作，不抢内容。产品页的标题不超过当前任务需要，重复的页面名、同义说明、强卡片要删。来源：https://vercel.com/geist/typography 与 https://linear.app/now/behind-the-latest-design-refresh
- **AI-native 验收**：AI 不作为视觉风格，而作为工作流状态：生成中、依据来源、失败、可撤回/继续。Carbon AI Label 只解决 AI 识别与透明，不允许把 AI 标签当按钮或装饰。来源：https://carbondesignsystem.com/components/ai-label/usage/
- **移动端验收**：底部 tab 只定位；主操作必须靠近当前任务；顶部品牌不能挤压首屏内容；所有输入/选择控件必须有稳定高度和安全区。

## 2026-07-05 五次落地：岗位百科入口

岗位百科详情页的挂绳工牌是品牌记忆点，保留；入口页的一次性 162 张大卡片墙不符合产品态密度，也会放大 AI 模板感。因此入口页改为百科索引：筛选区承担查询，结果区用紧凑行式列表展示头像、岗位名、英文名、简介和考点数；只有进入详情时使用工牌。这个模式后续也作为“大型知识集合”的默认样式。

## Theme

单一**暖纸浅色**主题，无暗色模式。物理场景：求职者赛前坐在电脑前、或面试中开着提词——纸感底色像摊开的笔记本，沉静、可信、不刺眼。暗色不做（候场室是亮的、温暖的）。

色彩策略：**Restrained 起步，单屏可升到 Committed**。墨色压暖纸做绝大多数表达，强调色只在"这一屏最该看的点"出现。**方向**：当前强调色（ok 绿/warn 琥珀/live 红）只用于语义状态，要新增一支克制的"主强调"用于当前选中/主行动/版面重心，让界面有重心、脱离纯灰阶。

## Color

OKLCH 思考，代码现存为 hex（token 与 telos 对齐，保持）。

| Token | 值 | 角色 |
|---|---|---|
| `--paper` | `#F0EEE9` | 页面底（暖纸）。**身份色，保留**——不是 AI 米色默认，是与 telos 共享的品牌承诺 |
| `--card` | `#FFFFFF` | 卡片/面板表面 |
| `--ink` | `#141310` | 主文字、主按钮、强对比 |
| `--ink-2` | `#56524A` | 正文次级 |
| `--ink-3` | `#928E84` | 弱文字/标签——⚠️ 暖纸上对比偏低，正文勿用，逐处复核 |
| `--line` | `#141310` | 强分隔/描边 |
| `--line-soft` | `#E2DFD7` | 常规边框/分隔线 |
| `--hatch` | `#D5D1C7` | 更弱的填充/虚线 |
| `--ok` | `#2f7d4f` | 成功/在投/复盘（绿） |
| `--warn` | `#9a6a2f` | 提醒/备战/示例（琥珀） |
| `--live` | `#b4453a` | 录音中/破坏性/口径红线（砖红） |

规则：
- 暖纸上的灰字用墨阶（ink-2/ink-3），不引第二种灰。
- 强调色不做装饰，只做语义与重心。
- **方向**：减少"白卡 + 软边框"无差别铺陈；分组优先用留白 + 发丝分隔线 + 底色微差（如 `ink 6%` 凹槽），卡片留给真正可点/独立的对象。

## Typography

三字体，对比轴正确（衬线 + 几何无衬线 + 等宽）：

| 角色 | 字体 | 用法 |
|---|---|---|
| Display / 衬线 | **Fraunces** (opsz 9–144, 400–700, 含斜体) | Landing、品牌字、长文档/报告标题。**不再作为工作台通用 h1** |
| UI / 无衬线 | **Geist Sans** (400/500/600/700，Inter 回退) | 导航、按钮、正文、标签、数据、产品页标题——产品 UI 主力 |
| Mono / 等宽 | **Geist Mono** (400/500/600，JetBrains Mono 回退) | 公司名、日期、计数、状态、命令、kbd |

规则：
- 产品 UI 用固定 rem 阶（非流式 clamp），步进 ~1.125–1.2。
- 正文行长 65–75ch（`--w-read:880px` 兜底）。
- 产品态 h1 通常 21–28px，使用 Geist Sans；Fraunces 大标题只在 landing / markdown 报告 / 品牌展示里使用。h1–h3 用 `text-wrap:balance`，长正文 `text-wrap:pretty`。
- ⚠️ **当前 eyebrow 过载**：`.sect-t` 等 mono 大写宽字距小标签几乎每段都有（AI grammar）。**方向**：大幅收敛，只在真正需要分区语义处保留，换其它节奏手段（衬线小标题/留白/分隔线）。

## Components

每个交互组件要有：default / hover / focus / active / disabled / loading / error 全套；跨视图同一套词汇（同一个按钮形状、同一套表单控件）。

当前清单（保留并统一）：
- **按钮** `.btn`（墨底主、ghost 次、small）：圆角 10px，hover 抬 1px + 阴影。
- **导航** `.nav button`：胶囊高亮，选中墨底反白。
- **卡片家族** `.scard/.stat/.jobcard/.bankcard/.qcard/.loopcard/.roundcard`：⚠️ **同一配方滥用**（`--card + 1px line-soft + radius 16 + 同一组阴影 0 10px 34px`）→ 千卡一面。**方向**：按"是否真的是独立可点对象"分级——只有 jobcard/roundcard 这类配边框阴影；列表/分组/统计改版面化（分隔线、留白、底色微差）。
- **Tab** `.tabs`：下边框选中态，标准。
- **下拉** 原生 `appearance:base-select` + `::picker` 定制（Chrome 135+，老浏览器回退）。
- **开关** `.toggle`、**segmented**（实时助手/模拟面试配置）。
- **空状态** `.empty`：虚线框 + 引导，教界面用法（保持）。
- **prose**（md 渲染）：⚠️ `.q-lead` / blockquote 用 `border-left:3px` 侧边条——impeccable 点名的廉价模式，**方向**：换全边框/底色微差/前导图标。

要补的态：loading 用骨架屏非转圈；error/disabled 态统一。

## Layout

- 宽度双档 token：`--w-page:1200px`（页面容器）、`--w-read:880px`（正文阅读），所有视图共用、footer 置底。
- 响应式是结构性的（折叠侧栏、底部 Tab 栏、单列回退），非流式字号。断点 ~560/760/840/900。
- 移动端：底部 Tab 栏（telos 式）、设置/弹层改底部 sheet、`env(safe-area-inset-bottom)`。
- Flex 优先 1D，Grid 用于 2D；无断点网格用 `repeat(auto-fit,minmax(280px,1fr))`。
- 语义化 z-index 阶（dropdown → sticky → modal-backdrop → modal → toast → tooltip），别用 999/9999。
- **方向**：建立显式间距阶并制造节奏（区与区之间留白有变化），治"拥挤或松散"。

## Motion

- 缓动 `--ease:cubic-bezier(.32,0,.18,1)`（ease-out 系，无弹跳）。产品过渡 150–250ms。
- 动效只传达状态（状态变化/反馈/加载/揭示），不做装饰；无编排式页面入场。
- 现有 `fadein` 视图切换、`lvpulse` 录音脉冲、流式光标——保留。
- `prefers-reduced-motion:reduce` 每个动效都要降级（淡入或瞬变）。
- 临场态尤其稳：提词不自动滚、不抢注意力。

## Signature（记忆点·方向）

治"显得普通/像 AI"需要一个可重复的品牌手势。候选：greenroom 候场/幕布隐喻（图标已有幕布 motif）、Fraunces 斜体品牌字、墨压暖纸的高对比标题。本轮要确立一个一致出现的招牌动作，让控制台一眼认得出是 greenroom。
