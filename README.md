# KKSRAG

![Python Version](https://img.shields.io/badge/python-3.10-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**KKSRAG** (KaKaXi RAG) 是一个极简的检索增强生成（RAG）框架。

相较于 LightRAG 等功能强大的工业级解决方案，KKSRAG 在功能上有所欠缺，但其核心优势在于**零外部依赖**和**纯 Python 部署**。

它无需安装 Elasticsearch、Neo4j 等复杂的数据库环境，内置了轻量级的搜索引擎，专为解决个人开发调试或学术研究中的小型测试需求而生。

## 特性

- **纯 Python 部署**：无需 Docker，无需任何外部数据库服务。
- **内置搜索引擎**：集成了轻量级索引与检索功能，开箱即用。
- **极简依赖**：基于标准 Python 生态构建，不依赖繁重的 C++ 扩展或复杂的向量库。
- **开箱即用**：下载源码即可运行，几行代码完成从文档索引到问答的流程。
- **透明高效**：代码结构简单，非常适合阅读源码、算法学习和快速修改。

## 为什么选择 KKSRAG？

目前的 RAG 生态中，像 LightRAG 这样的框架非常优秀，具备知识图谱融合和高并发能力。但对于**个人测试**或**学术原型验证**来说，它们往往过于“重”了。

| 特性 | KKSRAG | LightRAG / 其他工业框架 |
| :--- | :--- | :--- |
| 部署难度 | 极低 (仅需 Python 环境) | 中/高 (需配置 ES/Neo4j 等) |
| 外部依赖 | 少 (自带搜索引擎) | 多 (依赖向量库/图数据库) |
| 适用场景 | 个人笔记、代码调试、小规模论文实验 | 企业生产环境、大规模知识库 |

**核心优势**：KKSRAG 牺牲了一些高级功能（如知识图谱自动构建、极致的召回率优化），换来了**极度的便携性**。

## 快速开始

### 安装

#### 通过 pip 安装

```bash
git clone https://github.com/xyp-carry/KKSRAG.git
cd KKSRAG
pip install -r requirements.txt
```

#### 运行
```python
python main.py
```

#### 结果
```python
INFO:     Started server process [xxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:12250 (Press CTRL+C to quit)
```

#### 打开前端页面
```
cd server
python server.py
```

#### 结果演示
![前端页面](images/main.png)
#### 模型参数配置

在/config/config.json中配置
```json
{
    "base_url": "https://api.openai.com" ,
    "model": "gpt-4o",
    "api_key": "sk-xxxxxxxxxxxxxxxxxxx"
}
```
# 微信操作模块
## 1. 功能介绍
*   **自动回复**：后台发出消息，可通过识别关键词来触发消息回复。
*   **历史消息获取**：历史消息获取，可以获取较近用户发送的消息。
*   **实时消息获取**：用户可以通过微信发送消息，系统会实时将消息显示。
```
# 示例
from KKShandler.KKSwx import KKSWx

KKSwx = KKSWx()


"""获取指定窗口的历史记录"""
hwnd = KKSwx.phandler.find_all_windows_by_keyword("robot_test")[0]['hwnd']
history = KKSwx.get_history(hwnd, roll_times=5)
print(history)


"""发送文本到指定窗口"""
KKSwx.send_text(hwnd, '你好')



"""监测指定窗口的新消息，键盘输入ctrl+alt+q退出"""
wxqueue = [[]]
KKSwx.start(wxqueues= wxqueue,name=['robot_test'])

```
可以通过rag接口，或外部接入其他LLM及LLM产品的api进行消息回复。
## 注意：
本模块所有代码及相关衍生内容，仅限正向、合法、合规的技术研究与业务开发使用，严禁将本模块代码用于任何违法违规、损害国家利益、社会公共利益及他人合法权益的场景，包括但不限于网络攻击、恶意渗透、信息窃取、欺诈诱导、内容篡改等不正当用途。

本模块开发与维护方不对任何因违规使用、恶意利用本代码所产生的后果承担任何责任，一切因非正向使用引发的法律风险、经济损失、民事纠纷等，均由使用者自行承担全部责任。

使用者在使用本模块代码前，应充分知晓并遵守相关法律法规及行业规范，秉持合法合规、诚实守信的原则开展相关操作，自觉维护网络空间的安全与秩序
# 检索性能评估

## 1. 实验数据集说明

本次实验选取 **T2Ranking** 数据集作为评估基准。为了确保实验的可控性与效率，我们对该数据集进行了采样与截取：
*   **文档库**：选取数据集中前 **1,030** 条文档内容作为检索池。
*   **查询集**：选取关联的 **272** 条查询作为测试用例。

该数据规模能够有效模拟真实检索场景下的语义匹配需求，同时保证了实验的快速迭代。

## 2. 评估指标

针对大模型检索增强生成（RAG）场景对信息查全率的高要求，我们采用 **Recall@10** 作为核心评价指标。

**指标定义：**
计算在检索返回的前 10 个结果中，包含的正确相关文档数量占该查询所有相关文档总数的比例。
*   *计算逻辑：若某 Query 有 4 个正确选项，Top 10 中找全 4 个则得分为 1.0，仅找到 2 个则得分为 0.5。*

该指标直接反映了检索系统为下游大模型提供完整上下文信息的能力。

## 3. 实验结果与对比

我们对比了“纯关键词匹配”与“语义向量检索”两种模式下的性能表现，实验结果如下：

| 检索模式 | Recall@10 指标 | 性能提升 |
| :--- | :--- | :--- |
| **无 Embedding (基线)** | **75.60%** | - |
| **有 Embedding (语义检索)** | **90.09%** | **+14.49%** |

## 4. 结论

本次实验基于 T2Ranking 数据集，对比了关键词检索与语义向量检索在 RAG 场景下的性能。结论如下：

1.  **算法有效性验证**：目前的实验结果足以证明该检索算法的有效性。在复杂的语义匹配任务中，不论是传统关键词检索还是增加了embedding的语义理解检索，都能很好的满足 RAG 系统对检索模块的高标准要求。

