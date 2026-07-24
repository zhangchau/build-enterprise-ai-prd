# Rule + RAG + LLM + Schema 深化规范

## 目录

1. 第一性原理与双链路
2. 规则驱动审查
3. 知识源与权威治理
4. 清洗、结构化与冲突
5. Chunk 与上下文控制
6. Embedding 选型与评测
7. 向量库、索引和 Metadata
8. 检索、召回与 Rerank
9. Evidence Package 与 Prompt
10. Schema 与业务校验
11. 全链路异常和 Case
12. 文档与面试产物

## 1. 第一性原理与双链路

Rule、RAG 和 LLM 解决的是不同问题：

| 能力 | 核心职责 | 不应负责 |
| --- | --- | --- |
| Rule Engine | 执行正式、确定、可审计的业务政策 | 理解任意长文、自由生成解释 |
| RAG | 找到当前任务有权使用的相关证据 | 决定企业最终规则或绕过权限 |
| LLM | 理解非结构文本、组织证据、生成受控草稿 | 成为权限系统、规则库、事实源或事务状态机 |
| Validator | 拦截结构、引用、事实、规则和权限错误 | 用一个总分“判断一切” |
| Human | 确认高风险、冲突、例外和未知事实 | 替系统从零收集所有上下文 |

必须分别画：

### 离线知识生产

`Source Registry → 授权/病毒/DLP → 解析/OCR → 结构化 → 质量/冲突/脱敏 → Chunk → Embedding → Index → 评测 → 审批发布 → 版本/回滚/删除对账`

### 在线审查/问答

`用户/系统输入 → Intake/权限/版本 → 文件解析与 Fact → Rule Engine → Query → ACL/metadata filter → Hybrid Retrieval → Rerank → Evidence Package → Prompt/LLM → Schema/引用/业务校验 → 人工/Workflow → 写回/通知 → Trace/反馈/评测`

在图中写清对象流向和存储位置，不能只摆组件名称。

## 2. 规则驱动审查

### 规则审查到底做什么

把企业已批准的政策转成：

`适用范围 scope + 条件 condition + 事实 fact + 结论 decision + 风险 severity + 动作 action + 依据 citation + 例外/审批 + 版本`

规则输入不能直接是整份原文；优先使用经来源定位的结构化事实候选。LLM 可抽取候选，但规则的命中和动作必须可回放。

### 规则对象最低字段

| 类别 | 字段 |
| --- | --- |
| 身份 | rule_id、name、owner、status、version |
| 适用 | contract_type、party_role、jurisdiction、business_unit、effective_time |
| 条件 | fact path、operator、threshold、null/conflict behavior |
| 输出 | severity、decision、action、reason、required evidence |
| 治理 | source、approver、test cases、rollback_version、expiry |

### 三类教学 Case

1. **责任上限**：同一数字在采购方/销售方角色下可能产生相反动作，说明 scope 和角色不能由模型猜。
2. **自动续约**：通知期 59/60/61 日及政策生效日期，说明边界、版本和确定性测试。
3. **数据删除**：正文、附件和 DPA 共同定义义务，说明一个风险可能跨多个 Clause，缺附件不能等于无风险。

每个 Case 写：

- 原文/事实候选；
- 适用规则与版本；
- Rule trace；
- RAG 提供的说明/模板/案例；
- LLM 允许做的解释；
- Validator 必须拦截什么；
- 人工何时介入；
- 结果如何写回。

### 为什么需要相似案例

相似案例用于解释历史如何处理、提供谈判措辞和差异参考，不等于正式规则。案例必须带：

- 当时规则版本；
- 合同角色、类型、法域、金额/业务背景；
- 处理结论和是否特批；
- 是否仍有效；
- 权限和脱敏；
- 原文/修改文本和审批证据。

历史签过不代表当前允许；一次特批不能升级为通用规则。

## 3. 知识源与权威治理

先做知识地图，禁止直接“收集文档并 Embedding”：

| 知识类型 | 典型来源 | 权威性 | 更新 | 冲突 owner | 可否生成动作 |
| --- | --- | --- | --- | --- | --- |
| 正式规则/政策 | 法务、合规、制度平台 | 高 | 生效/失效驱动 | 规则 owner | 经 Rule Engine |
| 标准模板/条款库 | 法务模板系统 | 高 | 版本发布 | 模板 owner | 可形成建议草稿 |
| 指引/FAQ | 专家知识库 | 中 | 定期 | 内容 owner | 解释参考 |
| 历史案例 | CLM/工单/审批 | 条件性 | 持续 | 案例运营+专家 | 仅参考，需标签 |
| 外部法规/网页 | 官方来源 | 需确认适用 | 变更监测 | 法务 | 不直接自动决策 |
| 用户上传文档 | 当前任务 | 事实候选 | 按任务 | 当前用户/专家 | 不可信输入 |

### 数据收集要写

- 谁授权、通过什么接口/导出；
- 全量还是抽样，覆盖哪些时间、部门、类型；
- 原文件、解析文本、结构化对象分别存哪里；
- 是否包含个人信息、商业秘密、第三方版权；
- 数据出域、保留和删除；
- 失败/缺失/重复如何记录；
- source_id、hash、版本和血缘。

### 数据冲突优先级

不能只写“以最新为准”。建议按：

1. 法律/监管适用性；
2. 企业批准层级和 authoritative status；
3. scope specificity；
4. effective/expiry；
5. 当前业务上下文；
6. 仍冲突则 `CONFLICT`，交 owner 裁决。

规则与案例冲突时，正式现行规则优先，案例显示差异和例外原因。

## 4. 清洗、结构化与冲突

### 清洗不是去空格

至少处理：

- 文件真实性、格式、病毒、密码和损坏；
- OCR 页/区域置信与数字/单位；
- 页眉页脚、目录、批注、修订、印章；
- 表格、列表、定义、交叉引用和附件；
- 重复、近重复、同名异文；
- 编码、语言、日期/金额/期限标准化；
- PII/秘密脱敏并保留受控映射；
- 失效、撤销、特批和冲突标签；
- 解析结果与原文 span 双向定位。

### 结构化对象

不要只保留纯文本 Chunk。建议至少有：

- Document：source、hash、owner、version、ACL、status；
- Section/Clause：层级、title、span、parent/child、cross_reference；
- Fact Candidate：field、value、unit、source_span、confidence、confirmed；
- Rule/Template/Case：各自专用元数据；
- Chunk：text、parent、neighbors、token count、embedding/index version；
- Evidence：evidence_id、source_type、authority、support_span、permission；
- Review Result：对象版本、rule result、LLM draft、validator、human state。

### 常见难题与处理

| 难题 | 不能只做 | 正确策略 |
| --- | --- | --- |
| OCR 数字错 | 提高平均 OCR 分 | 数字/金额/日期专检、低质区域任务、原图定位 |
| 跨页条款断裂 | 固定长度切片 | 结构重建、邻接、父子关系 |
| 表格语义丢失 | 转成无表头纯文本 | 表头继承、行列坐标、表格专用表示 |
| 定义被远距离引用 | 盲目扩大窗口 | 定义链接和按需补充 |
| 正文引用附件 | 只解析正文 | 附件清单、cross-reference、缺失状态 |
| 同一文档多版本 | 覆盖旧文件 | 版本 DAG、hash、生效/撤销 |
| 脱敏破坏语义 | 全部替换为星号 | 类型一致占位符和受控映射 |

## 5. Chunk 与上下文控制

### 组合策略

| 策略 | 适合 | 风险 | Why |
| --- | --- | --- | --- |
| 结构切片 | 章节、条款、FAQ | 结构解析错会连锁 | 保留业务语义单元 |
| 语义切片 | 无清晰结构文本 | 边界不稳定 | 减少主题混合 |
| 滑动窗口 | 连续叙述、跨边界 | 重复和成本 | 补局部上下文 |
| 父子切片 | 长条款/长政策 | 索引和组装复杂 | 子块召回、父块解释 |
| 句窗/邻接 | 问答和证据定位 | 可能缺远距定义 | 控制 Token |
| 表格专用 | 费率/权限/阈值 | 通用 embedding 未必理解 | 保留表头和行列 |
| 关系补充 | 定义、附件、交叉引用 | 图关系维护成本 | 解决非相邻依赖 |

不要先决定 500 tokens。选型流程：

1. 定义检索任务和 Gold evidence span；
2. 统计文档结构、长度、跨段关系和表格；
3. 设计 2—4 个候选组合；
4. 建代表样本和 hard negative；
5. 比较 Recall@K、上下文完整、噪声、Token、时延；
6. 对 R1、长文、扫描件分层；
7. 选主策略和例外策略；
8. 记录重评条件。

### 上下文记忆与爆炸

区分：

- 当前请求业务上下文；
- 文档证据上下文；
- 多轮会话历史；
- 用户偏好/长期记忆。

控制方法：

- 结构化状态代替全文历史；
- Query 重写只保留当前任务必要槽位；
- 去重、相邻合并、父子按需展开；
- 先规则/metadata 过滤，再扩大语义候选；
- Token 预算按 System/Task/Evidence/Output 分配；
- 权威和 R1 证据优先，案例不能挤掉规则；
- 超预算时显式丢弃低优证据并留 trace；
- 摘要必须带来源，不能把摘要当权威事实；
- 新业务对象或权限变化时重置不适用记忆。

## 6. Embedding 选型与评测

### 硬约束先行

- 中文/多语言和领域文本；
- 最大输入、向量维度、归一化；
- 私有化/出域和许可证；
- 吞吐、时延、批处理、成本；
- 版本可冻结和主备兼容；
- 向量库/硬件支持；
- Query/Document 指令格式。

### 候选池

不要伪造当前候选的最新能力。先从官方文档或批准清单形成 3—5 个候选；写版本、日期和证据。受强时效影响时需要查询一手资料。

### 业务评测集

包括：

- 同义、简称、错别字；
- 长短 Query；
- 同文本不同角色/法域；
- 数字/表格/定义/附件；
- 过期、特批、无权限；
- 无答案；
- hard negative；
- 高风险低频样本。

指标：

- Recall@K 为首要召回指标；
- MRR/nDCG 看排序；
- 分层 R1 Recall；
- 无答案/拒答；
- 向量生成和检索时延；
- 存储、重建和单位成本。

最终选择要说明为何最强通用 Benchmark 不一定胜出，例如出域、中文业务集、时延或成本不满足。

## 7. 向量库、索引和 Metadata

### Metadata 最低集合

`tenant_id, source_id, document_id, document_version, source_type, authority, status, effective_at, expires_at, owner, business_scope, contract_type, party_role, jurisdiction, language, confidentiality, acl, parent_id, section_path, rule_version, exception_flag, embedding_version, index_version`

不是所有字段都要塞进向量；区分：

- 过滤字段；
- 排序特征；
- 展示字段；
- 审计/血缘字段。

### 索引设计要回答

- 使用何种 ANN/全文索引及原因；
- 按租户/业务分区还是共享；
- metadata pre-filter 和 post-filter；
- 增量、全量、双索引切换；
- embedding 版本变更如何重建；
- tombstone、物理删除、缓存失效；
- 索引与权威库如何对账；
- 备份、恢复和一致性；
- TopK、ef/search 参数怎样通过业务评测确定。

不要把 metadata filter 当成完整权限系统；结果返回前再次鉴权。

## 8. 检索、召回与 Rerank

### 在线过程

1. 识别任务、实体、角色、时间和权限；
2. 判断是否缺关键槽位，需要补问；
3. 生成原 Query、关键词 Query、结构化 filter；
4. Dense + Sparse/BM25 + 规则/精确索引多路召回；
5. 合并去重并记录各路排名；
6. 权限、status、effective、scope 硬过滤；
7. Rerank 处理语义、权威、角色、时间和差异；
8. 阈值/无答案判断；
9. 上下文组装与 Token 预算；
10. 输出 Evidence Package 和 trace。

### Rerank 评测

候选方法可包括 cross-encoder、LLM rerank、业务打分或组合。比较：

- Top1/TopK 支持率；
- R1 evidence recall；
- 相反角色/过期/特批 hard negative；
- 时延和成本；
- 长文本截断；
- 输出稳定性。

不是 TopK 越大越好。必须做 K 的边际收益与 Token/时延消融。

### 无召回与低质量

先判断：

- 正确知识不存在；
- 存在但解析/Chunk 错；
- filter/ACL 误杀；
- Query 错；
- embedding/BM25 未召回；
- Rerank 排掉；
- 上下文组装丢弃。

无证据时输出“未找到已发布适用证据/无法判断”，不能凑低分结果。

## 9. Evidence Package 与 Prompt

### Evidence Package

在进 LLM 前形成结构化、可校验的证据包：

- task、user intent、business context；
- object_id/version；
- confirmed facts 与 candidate facts；
- rule decisions 与 trace；
- allowed evidence_id 列表；
- authority、status、effective、scope；
- source span、引用位置；
- case similarities/differences/exception；
- permission；
- conflict/missing/low_quality；
- Token budget 和省略记录。

### Prompt 责任

推荐层次：

1. **System**：角色、禁止行为、证据边界；
2. **Task**：本次任务、风险和用户；
3. **Business Invariants**：规则结果、权限和不可更改字段；
4. **Evidence**：带 ID 和状态的证据；
5. **Output Contract**：字段、枚举、拒答/冲突状态；
6. **Examples**：只用已验证、不会泄漏测试答案的样例。

关键要求：

- 只能引用 allowlist 中的 evidence_id；
- 案例必须说明参考性质和差异；
- 证据不足/冲突时必须输出专门状态；
- 不得执行文档中的 Prompt-like 指令；
- 不得自行改变 severity、审批或权限；
- 输出不得包含未提供的事实。

Prompt 变更必须版本化并通过冻结集和灰度，不能因为“更流畅”直接发布。

## 10. Schema 与业务校验

若用户写“Sigma 校验”，先确认是否实际指 **Schema 校验（结构化输出约束）**，不要默默混用术语。

### 七层校验

| 层 | 检查 | Case |
| --- | --- | --- |
| 1 语法 | JSON/结构可解析 | 多余文本、截断 |
| 2 结构/类型 | required、type、array/object | severity 变成自由文本 |
| 3 值域 | enum、长度、格式、范围 | 风险级别越界 |
| 4 引用一致 | ID 存在、属于当前包/对象/版本 | 编造 rule_id |
| 5 证据支持 | 结论能由 span/规则支持 | 有引用但不支持结论 |
| 6 业务不变量 | 规则动作、版本、状态、审批不能被改 | 案例升级为强制规则 |
| 7 权限/动作 | 用户可见、可执行、需确认/幂等 | 普通用户关闭红线 |

结构正确不等于业务正确。校验必须保存失败字段、错误码、原始输出 hash 和组件版本。

### 失败处理

| 失败 | 可否重试 | 处理 |
| --- | --- | --- |
| 纯语法/局部格式 | 可有限字段级重试 | 约束生成/修复后再全校验 |
| 引用不存在 | 不能仅重问 | 拦截、重建 Evidence 或转人工 |
| 证据不足 | 不应强答 | `INSUFFICIENT_EVIDENCE` |
| 规则冲突 | 不能由 LLM 裁决 | `RULE_CONFLICT` 给 owner |
| 权限失败 | 禁止降级披露 | 拒绝、审计 |
| 外部写动作校验失败 | 禁止执行 | 保留草稿、人工确认 |

## 11. 全链路异常和 Case

至少覆盖：

1. 缺少我方角色，规则方向相反；
2. 扫描附件 OCR 数字错误，表面像“模型漏检”；
3. 相似案例来自相反角色；
4. 历史案例是一次特批；
5. 知识已下线但向量分片/缓存仍召回；
6. 模型编造 evidence_id；
7. Prompt Injection 要求泄露知识库；
8. 老任务晚到覆盖新对象版本；
9. 工具超时但实际写入成功；
10. 权限撤销后缓存仍显示结果；
11. 服务恢复时人工已处理；
12. 扩大 TopK 提升召回但成本/噪声恶化。

每个 Case 使用异常八格并给错误修法：

- 不要看到漏检就扩 TopK；
- 不要看到错答就调 Prompt；
- 不要看到超时就无限重试；
- 不要看到无召回就声称无风险；
- 不要把“转人工”当成完成。

## 12. 文档与面试产物

完成此模块至少有：

- 一张本人可重画的全链路图；
- 一张离线知识生产图；
- 一张在线请求/调用时序；
- 规则对象、Evidence Package 和输出 Schema；
- 数据源和权威矩阵；
- Chunk/Embedding/Rerank 候选与消融；
- 评测集分层和 hard negative；
- 三个正常规则 Case、五个异常/Corner Case；
- Prompt 模板及责任边界；
- Schema 七层校验和失败处理；
- 版本/Trace/权限/对账字段；
- Decision Log。

面试主线：

`为什么不能只用大模型 → Rule/RAG/LLM 怎样分工 → 数据怎样可信 → 为什么这样 Chunk/Embedding/Rerank → 如何评测 → 错误怎样定位到第一层 → 如何降级/人工/恢复 → 哪个证据会让你推翻方案`
