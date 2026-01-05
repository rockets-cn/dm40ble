#!/usr/bin/env python3
"""
简单测试 dm40ble 模块
"""
import asyncio
from dm40ble import Com_DM40A

async def test_dm40():
    """测试 DM40 连接"""
    print("🔍 开始测试 DM40...")
    device = Com_DM40A()

    try:
        # 连接设备
        print("📡 连接中...")
        await device.connect()
        print("✅ 连接成功!")

        # 设置回调
        data_received = False

        def on_data(data, unit):
            nonlocal data_received
            data_received = True
            print(f"📊 收到数据: {data} {unit}")

        device.set_data_update_callback(on_data)

        # 测试读取数据
        print("\n📤 读取数据...")
        for i in range(5):
            data, unit = await device.get_data()
            if data is not None:
                print(f"  [{i+1}] 数据: {data} {unit}")
            else:
                print(f"  [{i+1}] 无数据")
            await asyncio.sleep(0.5)

        # 断开连接
        print("\n🔌 断开连接...")
        await device.disconnect()
        print("✅ 测试完成!")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_dm40())
