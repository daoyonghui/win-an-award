# PrintMind 外部公开样本初步测试

## 测试说明

- 共测试 **6** 个公开外部样本（Bambu Lab 官方 Wiki 的打印质量/材料指南图片）。
- 全部以 `data_source = external` 提交，用于**本地诊断能力测试**。
- external 数据**不参与真实实验统计，也不参与历史经验学习**（测试前后 `/stats`、`/experience-summary`、`/experiment-summary` 均保持不变，见文末隔离性验证）。
- 本测试仅用于**初步观察**视觉诊断在外部图片上的表现；样本数量很小，**不代表统计意义上的准确率**，也不能用于声称泛化能力。
- 由于公开图片通常缺少完整工艺参数，统一使用测试参数（material=PETG, nozzle_temp=240, bed_temp=80, print_speed=60, fan_speed=50, layer_height=0.20, retraction=0.8），**symptom_description 留空**（未向模型提供标准答案）。推荐参数不作为该互联网样本的真实工艺结论。
- 每张图片仅调用一次视觉 API，未重复调用。

## 结果表

| Sample | Source label | PrintMind | Severity | Confidence | Match |
| --- | --- | --- | --- | --- | --- |
| sample_01 | Bambu Wiki · PETG 表面拉丝/气泡 | stringing | medium | 0.90 | 一致 |
| sample_02 | Bambu Wiki · 局部拉丝或漏料 | stringing | high | 1.00 | 一致 |
| sample_03 | Bambu Wiki · First layer not sticking | stringing（规则回退） | low | — | 无法评价 |
| sample_04 | Bambu Wiki · 模型翘边/脱落 | stringing（规则回退） | low | — | 无法评价 |
| sample_05 | Bambu Wiki · 模型缺料 | under_extrusion | medium | 0.55 | 一致 |
| sample_06 | Bambu Wiki · 表面局部缺料 | stringing（规则回退） | low | — | 无法评价 |

> Confidence 为视觉模型自报置信度，**不能当作 accuracy**。
> sample_03 / sample_04 / sample_06 的 `—` 表示**视觉分析未返回可用结果**，系统自动回退到工艺参数规则诊断；这 3 个样本**无法评价其视觉识别表现**（其输出为规则回退结果，不是模型对该图的判断）。

## 逐样本说明

### sample_01（expected: stringing）
- 来源描述：受潮 PETG 表面出现拉丝、气泡。
- PrintMind：`stringing`，severity=medium，confidence=0.90。
- visual evidence：柱状件之间可见多条细丝横跨相邻柱体；表面粗糙并挂有毛丝/细丝残留。
- 判断：**一致**，视觉证据与来源描述吻合。

### sample_02（expected: stringing）
- 来源描述：局部拉丝或漏料。
- PrintMind：`stringing`，severity=high，confidence=1.00。
- visual evidence：尖塔与圆柱主体之间存在大量细密丝状物；尖角边缘有毛丝/拉丝缠绕。
- 判断：**一致**。

### sample_03（expected: first_layer_issue）
- 来源描述：首层不粘板。
- PrintMind：`stringing`，severity=low，confidence=—。
- 说明：**视觉分析未返回可用结果，已回退规则诊断**（`visual_evidence` 为空），输出为规则回退结果而非图像判断。
- 判断：**无法评价**（视觉不可用，本轮不能评价其视觉识别表现）。

### sample_04（expected: first_layer_issue）
- 来源描述：模型翘边/脱落（首层附着相关）。
- PrintMind：`stringing`，severity=low，confidence=—。
- 说明：同样为**视觉分析未返回可用结果 → 回退规则诊断**。
- 判断：**无法评价**（视觉不可用）。

### sample_05（expected: under_extrusion）
- 来源描述：模型缺料（流量不足）。
- PrintMind：`under_extrusion`，severity=medium，confidence=0.55。
- visual evidence：表面中部有水平方向断续痕迹与细小缝隙/断线，挤出线条凹陷、填充不全。
- 备注：视觉判定为“欠挤出”，但工艺规则更倾向“拉丝”，系统返回冲突提示并保留视觉结论。
- 判断：**一致**。

### sample_06（expected: under_extrusion）
- 来源描述：表面局部缺料（速度突变导致）。
- PrintMind：`stringing`，severity=low，confidence=—。
- 说明：同样为**视觉分析未返回可用结果 → 回退规则诊断**。
- 判断：**无法评价**（视觉不可用）。

## 总结

- 总外部样本：**6**
- 视觉诊断成功：**3 / 6**
- 视觉诊断成功样本中，主要缺陷与来源描述一致：**3 / 3**
- 视觉不可用并进入规则回退：**3 / 6**（sample_03、sample_04、sample_06）

按缺陷类别：

| 类别 | 视觉成功 | 一致 | 备注 |
| --- | --- | --- | --- |
| stringing | 2 | 2 | sample_01、sample_02 |
| under_extrusion | 1 | 1 | sample_05（sample_06 视觉不可用，未纳入视觉表现评价） |
| first_layer_issue | 0 | — | sample_03、sample_04 均未获得有效视觉结果，本轮**无法评价**其视觉识别表现 |

- 统计口径：一致 **3** / 部分一致 **0** / 不一致 **0** / 无法评价（视觉不可用）**3** / 不支持 **0**。
- 视觉识别表现仅能在**视觉诊断成功的 3 个样本**上评价：3 个样本的主要缺陷判断均与来源描述一致。

> 结论仅限于“本轮 6 个公开外部样本的初步观察”，样本量小，不代表统计意义，也不能据此声称泛化能力已被验证。

## 隔离性验证

测试前后调用接口，确认 external 数据未污染真实统计与经验学习：

| 接口 | 测试前 | 测试后 |
| --- | --- | --- |
| `GET /stats` | total=7, verified=1, improved=1, rate=1.0, avg_gain=13.0 | total=7, verified=1, improved=1, rate=1.0, avg_gain=13.0 |
| `GET /experience-summary` | insights=3 | insights=3 |
| `GET /experiment-summary` | timeline=9（REAL-001～009） | timeline=9（REAL-001～009） |

- `/stats` 真实统计不变；external 不计入 total/verified/improved/rate/avg。
- `/experience-summary`、`/experiment-summary` 不变。
- 6 条 external 诊断记录保留在历史记录中，均标记为「外部样本」。

## 视觉 API 调用次数

- 本轮共发起 **6** 次视觉 API 调用（每张图片 1 次），其中 3 次返回可用结果，3 次未返回可用结果并触发规则回退。
- 未重复调用同一张图片，未使用 Pro 模型，未自动重试失败样本。
