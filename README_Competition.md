# PrintMind

**基于多模态智能体与工艺闭环优化的 FDM 3D 打印质量控制系统**

> 版本：**PrintMind V1.0 Competition Release Candidate**

---

## 1. 项目简介

PrintMind 面向 Bambu Lab P1S + PETG 的 FDM 打印场景，围绕“拉丝”等常见缺陷，形成一条可解释、可验证的闭环：

1. **输入**：打印件照片 + 工艺参数
2. **多模态缺陷识别**：视觉智能体（DeepSeek 视觉模型）结合图像给出缺陷判断
3. **规则与真实实验经验融合**：PETG 工艺规则 + 真实单变量实验经验
4. **最小改动参数推荐**：每次闭环优先只调整一个“有真实实验支持”的参数
5. **再打印验证**：按推荐参数重新打印并评分
6. **历史经验回写**：结果写回数据库，持续更新经验

核心特点：**可解释**（给出视觉证据、风险评分与推荐依据）、**有据可依**（来自真实实验，而非凭空生成）、**闭环可验证**（推荐 → 再打印 → 评分 → 回写）。

---

## 2. 技术栈

| 层 | 技术 |
| --- | --- |
| 前端 | Vue 3 + Vite |
| 后端 | Python + FastAPI |
| 数据库 | SQLite（标准库 `sqlite3`） |
| AI | DeepSeek API（视觉分析，可回退规则诊断） |

无大型依赖；图表使用原生 SVG/CSS 实现。

---

## 3. 当前真实实验环境

| 项 | 值 |
| --- | --- |
| 打印机 | Bambu Lab P1S |
| 材料 | Bambu PETG HF |
| 颜色 | 红色 |
| 喷嘴 | 0.4 mm |

---

## 4. 当前候选参数

| 参数 | 值 |
| --- | --- |
| nozzle_temp | 245 ℃ |
| bed_temp | 70 ℃ |
| outer_wall_speed | 60 mm/s |
| fan | 40–60 % |
| layer_height | 0.16 mm |
| retraction | 0.8 mm |

> 以上参数由现有真实实验记录聚合得到（页面「实验结论总览 → 当前候选参数」）。
> 结论限定在“当前实验条件下”，不代表统计显著性，也不泛化到所有 PETG。

---

## 5. 实验链（REAL-001 ～ REAL-009）

| 编号 | 类型 | 评分 | 说明 |
| --- | --- | --- | --- |
| REAL-001 | 基准组 | 65 | 建立基准 |
| REAL-002 | 单变量实验 | 60 | 喷嘴降温 |
| REAL-003 | 单变量实验 | 40 | 回抽提高到 1.1 mm |
| REAL-004 | 重复性验证 | 68 | 恢复基准参数 |
| REAL-005 | 单变量实验 | 82 | 风扇提高到 40–60% |
| **REAL-006** | **系统闭环验证** | **78** | **正式闭环：65 → 78** |
| REAL-007 | 重复性验证 | 85 | 最佳重复结果 |
| REAL-008 | 重复性验证 | 80 | 第二次重复 |
| REAL-009 | 进一步参数探索 | 77 | 风扇进一步提高后未继续改善 |

重点：
- **REAL-006 = 正式系统闭环验证**：采用最小改动策略后，质量由 **65 → 78**。
- **REAL-007 / REAL-008 = 重复性验证**：相同推荐参数重复打印达到 **85 / 80**。
- **REAL-009 = 进一步参数探索**：风扇由 40–60% 提高到 40–70% 后未继续提升。

---

## 6. 启动步骤

### 方式一：一键启动（推荐）

双击项目根目录的：

```
start_printmind.bat
```

脚本会检查运行前置条件，并分别用两个命令行窗口启动后端与前端，随后自动打开浏览器。

### 方式二：手动启动

后端：

```powershell
cd F:\PrintMind\backend
.\.venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

前端：

```powershell
cd F:\PrintMind\frontend
npm run dev
```

访问：http://127.0.0.1:5173

### 演示前快速自检

双击：

```
check_printmind.bat
```

逐项检查 Python / Node / venv / node_modules / .env / 数据库 / REAL-001～009 / verified 等，仅检查、不修改任何文件或数据。

---

## 7. 比赛演示路线

```
首页
 → 实验结论总览（REAL-001～009 质量趋势）
 → 返回首页
 → 智能诊断（上传样件 + 填写参数）
 → 缺陷诊断结果 / 图片视觉证据
 → 历史实验经验 / 最小改动推荐 / 推荐依据
 → 历史记录（查看系统闭环验证结果）
```

详细分镜见 `docs/demo_script.md`；演示用图见 `docs/demo_assets.md`。

---

## 8. 常见问题

**Q1：前端能打开但诊断报错？**
确认后端窗口仍在运行（http://127.0.0.1:8000/health 应返回 `{"status":"ok"}`）。

**Q2：诊断结果没有视觉证据？**
可能未上传图片，或视觉模型未配置/不可用。系统会自动回退到 PETG 规则诊断，并在结果中给出提示。

**Q3：推荐参数没有变化？**
当历史实验经验中没有“改善”证据时，最小改动策略会保持当前参数（这是预期行为）。

**Q4：`npm` 在 PowerShell 报执行策略错误？**
使用 `start_printmind.bat`（在 cmd 中运行），或执行 `npm.cmd run dev`。

**Q5：修改了数据库会影响演示吗？**
演示依赖真实实验数据。除非确有必要，请勿修改 `data/printmind.db`。

---

## 9. API 不可用时兜底方案

- **视觉 API（DeepSeek）不可用**：自动回退规则诊断，历史经验与参数推荐仍可展示（见 `docs/demo_fallback.md` 场景 B）。
- **完全无网络**：仍可完整展示首页、实验结论总览、REAL-001～009、历史闭环记录、图片与质量趋势（见 `docs/demo_fallback.md` 场景 C）。

兜底细节与现场话术见 `docs/demo_fallback.md`。

---

## 10. 主要接口

| 接口 | 说明 |
| --- | --- |
| `GET /` | 服务信息 |
| `GET /health` | 健康检查 |
| `POST /diagnose` | 缺陷诊断（可含图片，multipart/JSON） |
| `GET /history` / `GET /history/{id}` | 历史记录 |
| `POST /history/{id}/result` | 系统优化验证结果回写 |
| `POST /history/{id}/experiment` | 实验记录回写 |
| `GET /stats` | 比赛统计（默认仅 real） |
| `GET /experience-summary` | 历史实验经验总结 |
| `GET /experiment-summary` | 实验结论总览 |

---

*PrintMind V1.0 Competition Release Candidate — 真实设备、真实实验、闭环优化、可解释推荐。*
