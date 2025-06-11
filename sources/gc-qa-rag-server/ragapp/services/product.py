from typing import List, Dict
from qdrant_client import QdrantClient
import logging

from ragapp.common.config import app_config

# Initialize logger
logger = logging.getLogger(__name__)

# 固定产品配置
FIXED_PRODUCTS = {
    "forguncy": {
        "id": "forguncy",
        "name": "Forguncy",
        "display_name": "ProductName.Forguncy",
    },
    "wyn": {"id": "wyn", "name": "Wyn", "display_name": "ProductName.Wyn"},
    "spreadjs": {
        "id": "spreadjs",
        "name": "SpreadJS",
        "display_name": "ProductName.SpreadJS",
    },
    "gcexcel": {
        "id": "gcexcel",
        "name": "GcExcel",
        "display_name": "ProductName.GcExcel",
    },
}


def get_generic_products() -> List[Dict]:
    """
    获取generic模式下的动态产品列表
    这里可以从数据库、配置文件或其他数据源获取
    """
    try:
        # 初始化向量数据库客户端
        url = app_config.vector_db.host
        client = QdrantClient(url)

        # 获取所有集合
        response = client.get_aliases()

        # 提取generic产品
        generic_products = []
        for alia in response.aliases:
            if alia.alias_name.startswith("generic_") and alia.alias_name.endswith(
                "_prod"
            ):
                # 从集合名提取产品ID: generic_productname_prod -> productname
                product_id = alia.alias_name[
                    8:-5
                ]  # 去掉 'generic_' 前缀和 '_prod' 后缀

                generic_products.append(
                    {
                        "id": product_id,
                        "name": product_id.title(),  # 首字母大写
                        "display_name": f"ProductName.{product_id.title()}",
                        "type": "generic",
                    }
                )

        return generic_products

    except Exception as e:
        logger.error(f"Error getting generic products: {e}")
        return []


def get_available_products(mode: str = "fixed") -> Dict:
    """
    获取可用的产品列表

    Args:
        mode: "fixed" 为固定产品模式，"generic" 为动态产品模式

    Returns:
        包含产品列表和模式信息的字典
    """
    try:
        if mode == "generic":
            products = get_generic_products()
            return {"mode": "generic", "products": products}
        else:
            # 固定产品模式
            products = [
                {
                    "id": product_id,
                    "name": product_info["name"],
                    "display_name": product_info["display_name"],
                    "type": "fixed",
                }
                for product_id, product_info in FIXED_PRODUCTS.items()
            ]

            return {"mode": "fixed", "products": products}

    except Exception as e:
        logger.error(f"Error getting available products: {e}")
        # 出错时返回固定产品列表
        products = [
            {
                "id": product_id,
                "name": product_info["name"],
                "display_name": product_info["display_name"],
                "type": "fixed",
            }
            for product_id, product_info in FIXED_PRODUCTS.items()
        ]

        return {"mode": "fixed", "products": products}
