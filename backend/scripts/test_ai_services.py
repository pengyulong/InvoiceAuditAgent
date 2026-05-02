"""测试百度OCR和DeepSeek API连接"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.services.ai_service import ai_service


async def test_baidu_ocr():
    """测试百度OCR"""
    print("\n=== 测试百度OCR ===")
    try:
        # 创建一个简单的测试图片（红色方块）
        from PIL import Image
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
            test_img = Image.new('RGB', (100, 100), color='red')
            test_img.save(f.name)
            temp_path = f.name

        async with ai_service.baidu_client:
            result = await ai_service.baidu_client.recognize_text(temp_path)
            print(f"百度OCR结果: {result[:200] if result else '无文字'}")

        os.unlink(temp_path)
        print("✓ 百度OCR测试成功")
        return True
    except Exception as e:
        print(f"✗ 百度OCR测试失败: {e}")
        return False


async def test_deepseek():
    """测试DeepSeek"""
    print("\n=== 测试DeepSeek ===")
    try:
        async with ai_service.deepseek_client:
            result = await ai_service.deepseek_client._make_request([
                {"role": "user", "content": "用JSON格式返回一个简单的测试结果，包含field字段值为success"}
            ], max_tokens=100)

            content = result["choices"][0]["message"]["content"]
            print(f"DeepSeek结果: {content}")
            print("✓ DeepSeek测试成功")
            return True
    except Exception as e:
        print(f"✗ DeepSeek测试失败: {e}")
        return False


async def test_extract_invoice():
    """测试发票信息提取"""
    print("\n=== 测试发票信息提取 ===")
    try:
        from PIL import Image
        import tempfile

        # 创建一个测试图片（模拟发票）
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
            test_img = Image.new('RGB', (800, 600), color='white')
            # 添加一些文字模拟
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(test_img)
            draw.text((50, 50), "发票号码: FP12345678", fill='black')
            draw.text((50, 100), "销售方: 测试公司", fill='black')
            draw.text((50, 150), "价税合计: 1000.00", fill='black')
            test_img.save(f.name)
            temp_path = f.name

        result = await ai_service.extract_invoice_info(temp_path)
        print(f"发票信息提取结果: {result}")
        os.unlink(temp_path)
        print("✓ 发票信息提取测试成功")
        return True
    except Exception as e:
        print(f"✗ 发票信息提取测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_full_flow():
    """测试完整流程"""
    print("\n=== 测试完整流程 ===")

    # 测试健康检查
    health = await ai_service.health_check()
    print(f"健康检查结果: {health}")

    baidu_ok = health.get("baidu_ocr_available", False)
    deepseek_ok = health.get("deepseek_available", False)

    if not baidu_ok:
        print("⚠ 百度OCR不可用")
    if not deepseek_ok:
        print("⚠ DeepSeek不可用")

    if baidu_ok:
        await test_baidu_ocr()

    if deepseek_ok:
        await test_deepseek()

    if baidu_ok and deepseek_ok:
        await test_extract_invoice()

    return baidu_ok, deepseek_ok


if __name__ == "__main__":
    print("开始测试AI服务...")
    baidu_ok, deepseek_ok = asyncio.run(test_full_flow())

    print("\n" + "="*50)
    if baidu_ok and deepseek_ok:
        print("✓ 所有AI服务测试通过")
    else:
        print("⚠ 部分AI服务测试失败，请检查API配置")
        sys.exit(1)
