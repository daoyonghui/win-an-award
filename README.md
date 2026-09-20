# PrintMind——面向 FDM 增材制造的多模态智能体与证据约束闭环工艺优化系统

> **PrintMind combines multimodal perception, real-world experiment memory,
> evidence-constrained decision making and human-in-the-loop optimization for FDM 3D printing.**

PrintMind 面向 **Bambu Lab P1S + PETG** 场景，把「照片 + 工艺参数」转化为**可追溯、可验证**的工艺优化建议，并通过真实打印实验持续更新经验记忆，形成人机在环的闭环优化。

---

## 核心亮点

- **Multimodal Process Perception** — 结合缺陷照片与工艺参数的多模态过程感知
- **Evidence-Constrained Decision** — 证据约束决策：建议必须由规则/实验证据支撑，不做无据推断
- **Single-variable Minimum-Perturbation Optimization** — 单变量、最小扰动优化，便于归因
- **Experiment-driven Experience Memory** — 以真实实验驱动的经验记忆（历史检索 + 复用）
- **Human-in-the-loop Closed-loop Optimization** — 人机在环闭环：建议 → 实打 → 记录 → 更新
- **Data Provenance Isolation** — 数据来源分层隔离，保证统计口径纯净
- **Graceful Degradation & Observability** — 优雅降级（无 API Key 时回退本地规则）与可观测性

---

## 真实实验结果

| 编号 | 实验 | 质量分 |
| --- | --- | --- |
| REAL-001 | baseline | **65** |
| REAL-002 | lower nozzle temperature | 60 |
| REAL-003 | increased retraction | 40 |
| REAL-005 | increased cooling | 82 |
| REAL-006 | **formal closed-loop validation** | **65 → 78** |

> **说明**：REAL-005 代表 *improvement trend*（改进趋势），
> **REAL-006 才是正式的系统闭环验证**（65 → 78）。

---

## 技术栈

**Frontend**
- Vue 3
- Vite
- Vue Router

**Backend**
- Python
- FastAPI
- SQLite

**AI**
- DeepSeek multimodal analysis
- local rule fallback（本地规则回退）

---

## 项目架构

```
照片 + 工艺参数
        ↓
Multimodal perception          （多模态感知）
        ↓
Evidence-constrained decision  （证据约束决策）
        ↓
Minimum-perturbation recommendation（最小扰动推荐）
        ↓
Physical print validation      （真实打印验证）
        ↓
Experiment memory update       （经验记忆更新）
        ↺ 回到 Multimodal perception（闭环）
```

---

## 快速启动（Windows）

> 首次配置：`setup_for_teammate.bat`（若原项目存在）

```bat
:: 环境检查
check_printmind.bat

:: 比赛演示（一键）
start_competition_demo.bat

:: 正常启动
start_printmind.bat
```

- 后端默认：`http://127.0.0.1:8000`
- 前端开发：`http://127.0.0.1:5173`

---

## 环境变量

复制示例文件：

```
backend/.env.example   →   backend/.env
```

然后在 `backend/.env` 中自行填写：

```
DEEPSEEK_API_KEY=
```

> **真实 API Key 不包含在本仓库中。** 未配置 Key 时，系统自动回退到本地规则诊断，不影响运行。

---

## 数据可信度（Provenance Isolation）

数据严格分为三层，**互不混用**：

| 层级 | 含义 |
| --- | --- |
| `real` | 真实打印实验采集，进入真实闭环统计与经验学习 |
| `simulated` | 仿真数据 |
| `external` | 外部/公开样本 |

> **`simulated` / `external` 不进入真实闭环统计与经验学习。**
> 真实闭环只使用 `real` 数据，保证结论可追溯、口径纯净。

---

## Disclaimer

- 当前真实实验规模仍然较小，项目处于**实验验证阶段**。
- 不把模型置信度描述为**系统准确率**。
- 不声称已完成严格的**因果推断**。
- 本项目用于研究与竞赛演示，工艺建议请结合实际情况判断。

---

## 目录结构（节选）

```
PrintMind/
├── backend/            # FastAPI 后端（main/config/schemas、database、diagnosis、learning、rules、vision）
│   └── .env.example    # 环境变量示例（占位符，无真实密钥）
├── frontend/           # Vue 3 + Vite 前端（src/views、components、router、i18n、assets/showcase）
├── docs/               # 文档
├── experiments/        # 实验记录
├── data/               # 数据（真实实验记忆 printmind.db 等）
├── check_printmind.bat
├── start_printmind.bat
├── start_competition_demo.bat
└── README.md
```

## License

仅用于学习、研究与竞赛演示。
