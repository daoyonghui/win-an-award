# PrintMind 固定演示素材清单

> 本文件仅**登记**现有真实数据，不复制、不修改任何实验数据。
> 图片通过本地接口访问：`http://127.0.0.1:8000/uploads/<文件名>`
> 所有图片存放于：`F:\PrintMind\data\uploads\`

---

## 1. REAL-001（基准组）

| 项 | 值 |
| --- | --- |
| experiment_id | REAL-001 |
| 数据库记录 | `experiment_records.id = 2`；关联 `diagnosis_records.id = 3` |
| 图片路径 | `data/uploads/20260915_214151_91ffde9f.jpg` |
| 评分 | 65 |
| 演示目的 | 展示**基准组**原始缺陷状态，作为后续对比起点 |

---

## 2. REAL-006（系统闭环验证）

| 项 | 值 |
| --- | --- |
| experiment_id | REAL-006 |
| 数据库记录 | `diagnosis_records.id = 12`（`verified = 1`，`quality_before = 65`，`quality_after = 78`） |
| 闭环前图片 | `data/uploads/20260916_113518_4a1dd3bb.jpg` |
| 闭环后图片 | `data/uploads/20260916_114255_907a8e49.jpg` |
| 评分 | 65 → 78 |
| 演示目的 | 展示**正式系统闭环验证**：推荐参数 → 再打印 → 质量提升 |

---

## 3. REAL-007（最佳重复结果）

| 项 | 值 |
| --- | --- |
| experiment_id | REAL-007 |
| 数据库记录 | `experiment_records.id = 7`（`repeatability`，`reference_record_id = 11`） |
| 图片路径 | `data/uploads/20260916_130114_b2774b95.jpg` |
| 评分 | 85 |
| 演示目的 | 展示**重复性验证**的最佳结果 |

---

## 4. REAL-008（第二次重复）

| 项 | 值 |
| --- | --- |
| experiment_id | REAL-008 |
| 数据库记录 | `experiment_records.id = 8`（`repeatability`，`reference_record_id = 11`） |
| 图片路径 | `data/uploads/20260916_130114_5b25f166.jpg` |
| 评分 | 80 |
| 演示目的 | 展示重复实验的**稳定性**（85 / 80） |

---

## 5. REAL-009（进一步参数探索）

| 项 | 值 |
| --- | --- |
| experiment_id | REAL-009 |
| 数据库记录 | `experiment_records.id = 9`（`single_variable`，`reference_record_id = 11`） |
| 图片路径 | `data/uploads/20260916_130114_4642817b.jpg` |
| 评分 | 77 |
| 演示目的 | 展示**继续加大风扇未继续改善**，说明当前实验条件下 40–60% 更合适 |

---

## 演示使用建议

1. **诊断页**：上传一张打印件照片用于现场演示（可用上表任一图片作为固定测试样例）。
2. **实验结论总览**：时间线会自动显示上述图片缩略图。
3. **历史记录**：打开 REAL-006 详情，展示闭环前后对比。

> 说明：以上文件名与数据库字段均为当前真实数据；如需变更请通过应用界面操作，不要手工修改数据库文件。
