# PrintMind 外部公开样本来源记录

> 本文件记录用于「外部公开样本鲁棒性测试」的公开图片来源。
> 图片仅用于**本地诊断能力测试**，不属于真实实验，不加入 REAL 实验图片，不参与统计与经验学习。
> 图片保存目录：`F:\PrintMind\data\external_tests\`

测试环境：Bambu Lab P1S + PETG；`data_source = external`。

| sample_id | 来源网站 | 页面标题 | 原始页面地址 | 页面描述的主要问题 | expected_defect | 是否 PETG | 备注 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| sample_01 | wiki.bambulab.com | PETG 使用指南（Bambu Lab Wiki） | https://wiki.bambulab.com/zh/filament/petg | 受潮 PETG 表面出现拉丝、气泡 | stringing | 是（PETG 专页） | 官方 PETG 指南，图片 `/filament-acc/petg/image-22.png` |
| sample_02 | wiki.bambulab.com | 打印质量与解决办法（Bambu Lab Wiki） | https://wiki.bambulab.com/zh/filament-acc/filament/print-quality | 局部拉丝或漏料 | stringing | 通用 FDM 缺陷（非 PETG 专页） | 官方打印质量总表，图片 `拉丝1.png` |
| sample_03 | wiki.bambulab.com | First Layer Not Sticking（Bambu Lab Wiki） | https://wiki.bambulab.com/en/knowledge-sharing/first-layer-not-sticking | 首层不粘板 | first_layer_issue | 通用 FDM 缺陷（非 PETG 专页） | 图片 `first_layer_not_sticking_to_the_plate.jpg` |
| sample_04 | wiki.bambulab.com | 打印质量与解决办法（Bambu Lab Wiki） | https://wiki.bambulab.com/zh/filament-acc/filament/print-quality | 模型翘边 / 脱落（首层附着相关） | first_layer_issue | 通用 FDM 缺陷（非 PETG 专页） | 图片 `翘边1.png` |
| sample_05 | wiki.bambulab.com | 打印质量与解决办法（Bambu Lab Wiki） | https://wiki.bambulab.com/zh/filament-acc/filament/print-quality | 模型缺料（流量不足） | under_extrusion | 通用 FDM 缺陷（非 PETG 专页） | 图片 `缺料1.png` |
| sample_06 | wiki.bambulab.com | PETG 使用指南（Bambu Lab Wiki） | https://wiki.bambulab.com/zh/filament/petg | 表面局部缺料（速度突变导致） | under_extrusion | 是（PETG 专页） | 图片 `/filament-acc/petg/image-6.png` |

## 来源与合规说明

- 全部图片来自 **Bambu Lab 官方 Wiki**（FDM 打印质量/材料指南），用于非商业的本地诊断能力测试。
- 原计划使用的 `forum.bambulab.com`（PETG 缺陷讨论帖）在本次网络环境下返回 **HTTP 403**，无法访问，因此改用 Bambu Lab 官方 Wiki 作为替代来源。
- 其中 sample_01、sample_06 来自 **PETG 专页**；其余为 **通用 FDM 缺陷**参考图（Bambu Lab 官方），并非 PETG 专页，已在表中标注，避免将其结论泛化为 PETG 专属结论。
- 未使用 AI 生成图片、商品宣传图或与 3D 打印无关的图片。
