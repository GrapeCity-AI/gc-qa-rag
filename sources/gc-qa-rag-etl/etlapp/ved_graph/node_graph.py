import json
import os
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import community as community_louvain
from apyori import apriori
from etlapp.common.config import app_config

# Preview features


def get_file_names_in_directory(directory):
    file_names = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_names.append(os.path.join(root, file))
    return file_names


def update_graph(G, data):
    # 解析JSON数据并加入节点和边
    for item in data:
        # 添加主元素节点
        main_id = item["payload"]["file_index"]
        main_name = item["payload"]["title"]
        if not G.has_node(main_id):
            G.add_node(main_id, name=main_name)

        # 添加hit元素及连接的边
        for hit in item["hits"]:
            hit_id = hit["payload"]["file_index"]
            hit_name = hit["payload"]["title"]
            score = hit["score"]

            # 添加hit元素节点
            if not G.has_node(hit_id):
                G.add_node(hit_id, name=hit_name)

            # 禁止自连接
            if main_id == hit_id:
                continue

            # 添加边及累加score
            if G.has_edge(main_id, hit_id):
                G[main_id][hit_id]["weight"] += score
            else:
                G.add_edge(main_id, hit_id, weight=score)


def paint(G):
    zh_font = fm.FontProperties(fname="C:/Windows/Fonts/simhei.ttf")  # Windows示例路径

    # 计算节点的度数
    degree_dict = dict(G.degree(G.nodes()))

    # 选择布局
    pos = nx.spring_layout(G, seed=42)  # 使用spring布局

    # 颜色映射：节点度越高颜色越深
    node_color = [degree_dict[node] for node in G.nodes()]

    # 节点大小映射：节点度越高节点越大
    node_size = [v * 100 for v in degree_dict.values()]

    # 可视化图
    pos = nx.spring_layout(G)
    labels = nx.get_node_attributes(G, "name")

    # 绘制节点
    nx.draw_networkx_nodes(
        G, pos, node_color=node_color, node_size=node_size, cmap=plt.cm.Blues
    )

    # 绘制边
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color="gray")

    # 绘制节点标签
    nx.draw_networkx_labels(
        G,
        pos,
        labels=labels,
        font_size=12,
        font_color="black",
        font_family=zh_font.get_name(),
    )

    # # 显示颜色条
    # sm = plt.cm.ScalarMappable(
    #     cmap=plt.cm.Blues, norm=plt.Normalize(vmin=min(node_color), vmax=max(node_color))
    # )
    # sm.set_array([])
    # plt.colorbar(sm, label="Node Degree")

    # 移除坐标轴
    plt.axis("off")

    # 设置标题，使用中文字体
    plt.title("NetworkX图形展示", fontproperties=zh_font, size=15)

    # 显示图像
    plt.show()


def paint_central(G):
    # 计算各种中心性指标
    degree_centrality = nx.degree_centrality(G)
    betweenness_centrality = nx.betweenness_centrality(G, weight="weight")
    closeness_centrality = nx.closeness_centrality(G)

    # 尝试增加迭代次数和调整收敛容差来计算特征向量中心性
    try:
        eigenvector_centrality = nx.eigenvector_centrality(
            G, max_iter=1000, tol=1e-06, weight="weight"
        )
    except nx.PowerIterationFailedConvergence as e:
        print(f"Error: {e}")
        eigenvector_centrality = None

    # 打印中心性指标
    print("Degree Centrality:")
    print(degree_centrality)
    print("\nBetweenness Centrality:")
    print(betweenness_centrality)
    print("\nCloseness Centrality:")
    print(closeness_centrality)
    if eigenvector_centrality:
        print("\nEigenvector Centrality:")
        print(eigenvector_centrality)
    else:
        print("\nEigenvector Centrality computation failed.")

    # 可视化图和中心性
    pos = nx.spring_layout(G)  # 或者选择其他布局，如circular_layout

    # 创建一个绘图对象和一个轴
    fig, ax = plt.subplots()
    node_color = [degree_centrality[node] for node in G.nodes()]
    nodes = nx.draw_networkx_nodes(
        G, pos, node_color=node_color, cmap=plt.cm.Blues, node_size=500, ax=ax
    )
    labels = nx.get_node_attributes(G, "name")
    nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5, ax=ax)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=12, ax=ax)

    # 添加Colorbar
    sm = plt.cm.ScalarMappable(
        cmap=plt.cm.Blues,
        norm=plt.Normalize(vmin=min(node_color), vmax=max(node_color)),
    )
    sm._A = []
    cbar = fig.colorbar(sm, ax=ax)
    cbar.set_label("Degree Centrality")

    plt.title("Network Visualization with Degree Centrality")
    plt.show()


def paint_community(G):
    # 1. 计算最佳分区
    partitions = community_louvain.best_partition(G, weight="weight")

    # 设置matplotlib的字体为支持中文的字体，例如SimHei
    plt.rcParams["font.sans-serif"] = ["SimHei"]  # 使用黑体
    plt.rcParams["axes.unicode_minus"] = False  # 防止负号显示成方块

    # 2. 给不同社区设置颜色
    # 获取社区数量
    num_communities = len(set(partitions.values()))
    colors = [plt.cm.rainbow(i / num_communities) for i in range(num_communities)]

    # 生成节点颜色列表
    node_color_map = [colors[partitions[node]] for node in G.nodes()]

    # 获取节点标签
    labels = nx.get_node_attributes(G, "name")

    # 3. 绘图
    plt.figure(figsize=(10, 10))
    nx.draw_spring(G, node_color=node_color_map, labels=labels, with_labels=True)
    plt.show()


def paint_relations(G):
    # 将图转换为关联规则挖掘所需的事务数据
    # 在本示例中，我们假设每个节点与其邻居节点构成一个事务
    transactions = []
    for node in G.nodes():
        neighbors = list(G.neighbors(node))
        if neighbors:  # 只添加有邻居的节点
            transactions.append(neighbors)

    print("Transactions:")
    for t in transactions:
        print(t)

    # 使用 Apriori 算法进行关联规则挖掘
    # 设置最小支持度，最小置信度和最小提升度（根据具体需求进行调整）
    min_support = 0.2
    min_confidence = 0.5
    min_lift = 1.0

    association_rules = apriori(
        transactions,
        min_support=min_support,
        min_confidence=min_confidence,
        min_lift=min_lift,
    )
    association_results = list(association_rules)

    # 打印关联规则
    print("\nAssociation Rules:")
    for item in association_results:
        pair = item[0]
        items = [x for x in pair]
        print("Rule: " + str(items))
        print("Support: " + str(item[1]))
        print("Confidence: " + str(item[2][0][2]))
        print("Lift: " + str(item[2][0][3]))
        print("=====================================")

    # 可视化图
    pos = nx.spring_layout(G)
    plt.figure(figsize=(8, 6))

    labels = nx.get_node_attributes(G, "name")
    nx.draw(
        G,
        pos,
        with_labels=True,
        labels=labels,
        node_size=500,
        node_color="skyblue",
        font_size=12,
        font_weight="bold",
    )
    plt.title("Network Graph Visualization")
    plt.show()


def find_increasing_pagerank_paths(G, node, current_pagerank=None, current_path=None):
    if current_path is None:
        current_path = []

    # 添加当前节点到路径
    current_path.append(node)

    # 获取当前节点的PageRank
    if current_pagerank is None:
        current_pagerank = G.nodes[node]["pagerank"]

    # 初始化结果列表
    paths = []

    # 遍历当前节点的所有邻居
    max_weighted_pagerank_neighbor = None
    max_weighted_pagerank_value = -1

    for neighbor in G.neighbors(node):
        # 获取边的权重
        edge_weight = G[node][neighbor]["weight"]

        # 计算加权PageRank
        weighted_pagerank = edge_weight * G.nodes[neighbor]["pagerank"]

        # 如果加权PageRank大于当前节点的PageRank
        if (
            weighted_pagerank > current_pagerank
            and weighted_pagerank > max_weighted_pagerank_value
        ):
            max_weighted_pagerank_value = weighted_pagerank
            max_weighted_pagerank_neighbor = neighbor

    # 如果找到了符合条件的邻居
    if max_weighted_pagerank_neighbor is not None:
        # 递归调用函数
        new_paths = find_increasing_pagerank_paths(
            G,
            max_weighted_pagerank_neighbor,
            max_weighted_pagerank_value,
            list(current_path),
        )
        # 将找到的新路径添加到结果列表
        paths.extend(new_paths)

    # 如果当前路径是一个递增的加权PageRank路径，将其添加到结果列表
    if len(current_path) > 1:
        paths.append(current_path)

    return paths


def start_generate_gexf():
    # 创建NetworkX图
    G = nx.DiGraph()

    # 读取JSON数据
    file_path = os.path.join(app_config.root_path, "ved_graph/.temp/forguncy/")

    files = get_file_names_in_directory(file_path)
    count = 0
    for filename in files:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            print(str(count) + ":" + filename)
            update_graph(G, data)
            count += 1
            if count > 2000:
                break
    pagerank = nx.pagerank(G, alpha=0.85)
    nx.set_node_attributes(G, pagerank, "pagerank")

    # 找出从每个节点开始的所有递增PageRank路径
    all_increasing_pagerank_paths = []

    for node in G.nodes():
        increasing_pagerank_paths = find_increasing_pagerank_paths(G, node, 0)
        all_increasing_pagerank_paths.extend(increasing_pagerank_paths)

    print("All Increasing PageRank Paths:")
    for path in all_increasing_pagerank_paths:
        # 使用 '->' 连接路径中的节点的名字
        formatted_path = " -> ".join(G.nodes[node]["name"] for node in path)
        print(formatted_path)

    # nx.write_gexf(G, "my_graph_di.gexf")
