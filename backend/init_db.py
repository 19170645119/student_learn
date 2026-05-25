import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import engine, Base
from models.learning_path import KnowledgeNode

COURSE_DATA = [
    {"title": "第1章 人工智能概述", "content": "人工智能的定义、发展历史、主要流派、应用领域、图灵测试、强AI与弱AI的区别", "level": "beginner", "order_num": 1, "node_type": "chapter"},
    {"title": "1.1 什么是人工智能", "content": "人工智能的定义与核心目标。AI是研究、开发用于模拟、延伸和扩展人的智能的理论、方法、技术及应用系统的一门技术科学。包括感知、推理、学习、决策等能力。", "level": "beginner", "order_num": 11, "node_type": "section", "parent_id": None},
    {"title": "1.2 AI发展历史", "content": "AI的三次浪潮：1956年达特茅斯会议→专家系统时代→机器学习崛起→深度学习革命→大模型时代", "level": "beginner", "order_num": 12, "node_type": "section", "parent_id": None},
    {"title": "1.3 AI应用领域", "content": "计算机视觉、自然语言处理、语音识别、推荐系统、自动驾驶、医疗诊断、金融风控等", "level": "beginner", "order_num": 13, "node_type": "section", "parent_id": None},

    {"title": "第2章 搜索与推理", "content": "状态空间搜索、启发式搜索、A*算法、博弈树搜索、Alpha-Beta剪枝、约束满足问题", "level": "beginner", "order_num": 2, "node_type": "chapter"},
    {"title": "2.1 状态空间搜索", "content": "状态空间表示法：用状态和操作符描述问题。无信息搜索策略：广度优先BFS、深度优先DFS、迭代深化。有信息搜索：贪心最佳优先、A*算法（f(n)=g(n)+h(n)），启发式函数设计原则（可采纳性、一致性）。", "level": "beginner", "order_num": 21, "node_type": "section", "parent_id": None},
    {"title": "2.2 博弈树搜索", "content": "Minimax算法：在博弈树中最大化己方收益、最小化对方收益。Alpha-Beta剪枝优化：通过维护α和β值剪除不可能影响最终决策的分支，将时间复杂度从O(b^d)降至O(b^(d/2))。", "level": "intermediate", "order_num": 22, "node_type": "section", "parent_id": None},

    {"title": "第3章 机器学习基础", "content": "监督学习、无监督学习、强化学习、过拟合与正则化、交叉验证、特征工程、评估指标", "level": "beginner", "order_num": 3, "node_type": "chapter"},
    {"title": "3.1 监督学习", "content": "分类与回归任务。线性回归：最小二乘法、梯度下降优化。逻辑回归：sigmoid函数、交叉熵损失。决策树：ID3（信息增益）、C4.5（增益率）、CART（Gini系数）。支持向量机SVM：最大间隔分类器、核技巧（线性核、RBF核、多项式核）。K近邻KNN：基于距离的懒惰学习。", "level": "intermediate", "order_num": 31, "node_type": "section", "parent_id": None},
    {"title": "3.2 无监督学习", "content": "K-Means聚类：随机初始化→分配→更新→收敛，肘部法则选K值。层次聚类：凝聚式（AGNES）、分裂式（DIANA）。PCA主成分分析：协方差矩阵特征分解降维。", "level": "intermediate", "order_num": 32, "node_type": "section", "parent_id": None},
    {"title": "3.3 模型评估与优化", "content": "过拟合（高方差）vs欠拟合（高偏差）。正则化：L1（Lasso稀疏解）和L2（Ridge权重衰减）。交叉验证：K-Fold、留一法。评估指标：准确率、精确率、召回率、F1-Score、ROC-AUC。", "level": "intermediate", "order_num": 33, "node_type": "section", "parent_id": None},

    {"title": "第4章 深度学习", "content": "神经网络基础、反向传播、CNN、RNN、LSTM、Transformer、注意力机制、预训练模型", "level": "intermediate", "order_num": 4, "node_type": "chapter"},
    {"title": "4.1 神经网络基础", "content": "感知机模型。多层感知机MLP：输入层→隐藏层→输出层。激活函数：Sigmoid（饱和梯度消失）、ReLU（稀疏激活）、Tanh、LeakyReLU。反向传播算法BP：链式法则计算梯度，随机梯度下降SGD更新权重。批量归一化BatchNorm、Dropout正则化。", "level": "intermediate", "order_num": 41, "node_type": "section", "parent_id": None},
    {"title": "4.2 卷积神经网络CNN", "content": "卷积层：卷积核（滤波器）滑动提取局部特征。池化层：最大池化、平均池化（降维+平移不变性）。全连接层。经典架构：LeNet-5→AlexNet→VGG→GoogLeNet(Inception)→ResNet(残差连接解决梯度消失)。", "level": "intermediate", "order_num": 42, "node_type": "section", "parent_id": None},

    {"title": "第5章 自然语言处理", "content": "文本预处理、词向量、Word2Vec、RNN/LSTM语言模型、Seq2Seq、注意力机制、Transformer架构", "level": "intermediate", "order_num": 5, "node_type": "chapter"},
    {"title": "5.1 词向量与语言模型", "content": "One-hot编码→词袋模型→TF-IDF。Word2Vec：CBOW（上下文预测目标词）和Skip-gram（目标词预测上下文），负采样优化。GloVe全局词向量：基于共现矩阵分解。N-gram语言模型：马尔可夫假设，困惑度Perplexity评估。", "level": "intermediate", "order_num": 51, "node_type": "section", "parent_id": None},
    {"title": "5.2 Transformer架构", "content": "Self-Attention：Q（Query）、K（Key）、V（Value）计算，Scaled Dot-Product Attention。Multi-Head Attention：多个注意力头并行捕捉不同子空间信息。Positional Encoding：正弦/余弦位置编码。Feed-Forward Network、Layer Normalization、残差连接。Encoder-Decoder结构。", "level": "advanced", "order_num": 52, "node_type": "section", "parent_id": None},

    {"title": "第6章 计算机视觉", "content": "图像处理基础、目标检测、图像分割、生成对抗网络GAN、扩散模型、多模态模型", "level": "intermediate", "order_num": 6, "node_type": "chapter"},
    {"title": "6.1 目标检测", "content": "两阶段检测器：R-CNN→Fast R-CNN→Faster R-CNN（RPN区域建议网络）。单阶段检测器：YOLO（You Only Look Once）将检测视为回归问题、SSD多尺度特征图。评估指标：IoU交并比、mAP平均精度均值。", "level": "intermediate", "order_num": 61, "node_type": "section", "parent_id": None},
    {"title": "6.2 图像生成", "content": "GAN生成对抗网络：生成器G和判别器D的博弈训练，minimax目标函数。DCGAN使用卷积架构。Conditional GAN、CycleGAN（无配对图像转换）。扩散模型Diffusion Model：前向加噪→反向去噪，DDPM、Stable Diffusion潜在空间扩散。", "level": "advanced", "order_num": 62, "node_type": "section", "parent_id": None},

    {"title": "第7章 强化学习", "content": "马尔可夫决策过程MDP、价值函数、Q-Learning、DQN、策略梯度、Actor-Critic", "level": "advanced", "order_num": 7, "node_type": "chapter"},
    {"title": "7.1 强化学习基础", "content": "MDP五元组：(S,A,P,R,γ)。状态、动作、状态转移概率、奖励函数、折扣因子。策略π(a|s)：状态到动作的映射。价值函数：状态价值V(s)、动作价值Q(s,a)。Bellman方程：V(s)=max_a[R(s,a)+γΣP(s'|s,a)V(s')]。", "level": "advanced", "order_num": 71, "node_type": "section", "parent_id": None},
    {"title": "7.2 深度强化学习", "content": "DQN：用神经网络近似Q函数，经验回放Experience Replay打破数据相关性，目标网络Target Network稳定训练。Policy Gradient：直接优化策略π_θ，REINFORCE算法。Actor-Critic：Actor(策略网络)+Critic(价值网络)结合，A3C异步训练，PPO近端策略优化。", "level": "advanced", "order_num": 72, "node_type": "section", "parent_id": None},

    {"title": "第8章 AI伦理与未来", "content": "AI伦理原则、算法公平性、可解释AI、隐私保护、AI安全、AGI展望、大模型的机遇与挑战", "level": "beginner", "order_num": 8, "node_type": "chapter"},
    {"title": "8.1 AI伦理问题", "content": "算法偏见与公平性：数据偏见→模型偏见→决策不公。可解释性XAI：LIME局部解释、SHAP博弈论解释。隐私保护：联邦学习（数据不动模型动）、差分隐私（添加噪声保护个体）。AI安全：鲁棒性对抗攻击、对齐问题Alignment。", "level": "intermediate", "order_num": 81, "node_type": "section", "parent_id": None},
    {"title": "8.2 前沿展望", "content": "大语言模型LLM：GPT系列、Claude、文心一言、星火等。多模态大模型：文本+图像+视频+语音统一理解与生成。具身智能Embodied AI：机器人与物理世界交互。AGI通用人工智能的路径探讨。AI Agent与工具使用的范式变革。", "level": "intermediate", "order_num": 82, "node_type": "section", "parent_id": None},
]


async def init_knowledge_base():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        from sqlalchemy import select, text
        result = await conn.execute(text("SELECT COUNT(*) FROM knowledge_node"))
        count = result.scalar()
        if count > 0:
            print(f"知识库已有 {count} 条数据，跳过导入")
            return

    # 先创建章节（parent_id=None）
    from sqlalchemy.ext.asyncio import AsyncSession
    from models import AsyncSessionFactory

    async with AsyncSessionFactory() as session:
        chapter_map = {}
        # 创建章节
        for item in COURSE_DATA:
            if item["node_type"] == "chapter":
                node = KnowledgeNode(
                    title=item["title"],
                    content=item["content"],
                    level=item["level"],
                    order_num=item["order_num"],
                    node_type=item["node_type"],
                )
                session.add(node)
                await session.flush()
                chapter_map[item["order_num"]] = node.id
                print(f"创建章节: {item['title']}")

        # 创建节，关联到对应章节
        chapter_parent_map = {
            11: 1, 12: 1, 13: 1,  # 第1章的子节点
            21: 2, 22: 2,          # 第2章
            31: 3, 32: 3, 33: 3,   # 第3章
            41: 4, 42: 4,          # 第4章
            51: 5, 52: 5,          # 第5章
            61: 6, 62: 6,          # 第6章
            71: 7, 72: 7,          # 第7章
            81: 8, 82: 8,          # 第8章
        }

        for item in COURSE_DATA:
            if item["node_type"] == "section":
                parent_order = chapter_parent_map.get(item["order_num"])
                parent_id = chapter_map.get(parent_order)
                node = KnowledgeNode(
                    title=item["title"],
                    content=item["content"],
                    level=item["level"],
                    order_num=item["order_num"],
                    node_type=item["node_type"],
                    parent_id=parent_id,
                )
                session.add(node)
                print(f"  创建小节: {item['title']} (parent: {parent_id})")

        await session.commit()
        print(f"\n✅ 知识库初始化完成！共导入 {len(COURSE_DATA)} 条数据")


if __name__ == "__main__":
    asyncio.run(init_knowledge_base())
