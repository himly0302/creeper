#!/usr/bin/env python3
"""
测试内容验证修复效果
"""
import sys
sys.path.append('src')
from src.fetcher import WebFetcher

def test_content_validation():
    """测试内容验证逻辑"""
    fetcher = WebFetcher()

    # 测试1: 错误页面内容（即使足够长也应该被过滤）
    error_content = """您查找的内容不存在，或已不再存在。

我们与精选广告合作伙伴会使用追踪器收集您的部分数据，以优化您的使用体验并推送个性化内容与广告。若您不希望这些信息被使用，请在继续访问前检查您的设备及浏览器隐私设置（新窗口）。

了解更多（新窗口）"""

    # 测试2: 正常内容（足够长且高质量）
    normal_content = """中美关税关系是当前国际经贸关系中的重要议题。双方在贸易政策方面的调整将对全球经济产生深远影响。

中美两国作为全球最大的两个经济体，其贸易政策的变化不仅影响着两国经济，也对全球贸易格局产生重大影响。近年来，中美贸易摩擦不断，双方在关税政策上的调整备受国际社会关注。

这种贸易关系的演变将继续影响全球供应链的重新布局和国际分工的调整。各国政府和企业都在密切关注这一发展趋势，并制定相应的应对策略。

贸易政策的变化涉及多个方面，包括关税税率、进出口配额、贸易壁垒等。这些政策措施的调整将直接影响到相关产业的发展和消费者的利益。因此，深入了解中美关税政策的最新动态对于企业和个人都具有重要意义。

在国际贸易环境中，关税政策的变化往往会引发连锁反应。一个国家的关税调整可能会促使其他国家采取相应的报复性措施，从而导致贸易战的升级。这种情况下，全球经济都将面临不确定性和风险。"""

    print("=== 内容验证测试 ===\n")

    print(f"错误内容长度: {len(error_content)} 字符")
    print(f"错误内容验证结果: {fetcher._is_valid_content(error_content)}")
    print("应该返回 False（过滤掉错误页面）\n")

    print(f"正常内容长度: {len(normal_content)} 字符")
    print(f"正常内容验证结果: {fetcher._is_valid_content(normal_content)}")
    print("应该返回 True（保留正常内容）\n")

    # 测试一些边界情况
    print("=== 边界情况测试 ===\n")

    # 测试包含404的内容
    content_404 = "404 Page Not Found. The requested URL was not found on this server." + "a" * 180
    print(f"包含404的内容验证结果: {fetcher._is_valid_content(content_404)}")
    print("应该返回 False\n")

    # 测试包含订阅要求的内容
    content_subscription = "请订阅我们的服务以获取完整内容。" + "b" * 180
    print(f"包含订阅要求的内容验证结果: {fetcher._is_valid_content(content_subscription)}")
    print("应该返回 False\n")

    # 测试短内容
    short_content = "太短的内容"
    print(f"短内容验证结果: {fetcher._is_valid_content(short_content)}")
    print("应该返回 False\n")

    print("测试完成！")

if __name__ == "__main__":
    test_content_validation()