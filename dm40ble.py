"""
DM40A 蓝牙万用表通信类
支持多种测量模式：电压、电流、电阻、电容、频率、温度等
"""
import asyncio
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic
from typing import Optional, Callable, Any, Tuple
import struct
import time

class Com_DM40A:
    # 测量模式常量
    MODE_DC_VOLTAGE = 1      # 直流电压
    MODE_AC_VOLTAGE = 2      # 交流电压
    MODE_DC_CURRENT = 3      # 直流电流
    MODE_AC_CURRENT = 4      # 交流电流
    MODE_RESISTANCE = 5      # 电阻
    MODE_CAPACITANCE = 6     # 电容
    MODE_FREQUENCY = 7       # 频率
    MODE_TEMPERATURE = 8     # 温度
    MODE_DIODE = 9           # 二极管
    MODE_CONTINUITY = 10     # 通断

    def __init__(self, device_addr: str = "EB31784A-359B-AAF1-E798-76064EA680CD", max_retry: int = 3):
        self._device_addr = device_addr
        self._client: Optional[BleakClient] = None
        self._rx_char: Optional[BleakGATTCharacteristic] = None
        self._tx_char: Optional[BleakGATTCharacteristic] = None
        self._response_event = asyncio.Event()
        self._response_data = bytearray()
        self.write_uuid = "0000fff1-0000-1000-8000-00805f9b34fb"
        self.read_uuid = "0000fff2-0000-1000-8000-00805f9b34fb"
        self._task = None
        self._current_data = None
        self._current_unit = ""
        self._current_mode = ""
        self._stop_event = asyncio.Event()
        self._data_update_callback = None
        self._mode = 0
        self._task_state = 0
        self.max_retry = max_retry

    def run(self, loop_ms=1000):
        """启动后台任务持续获取数据"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            import threading
            def run_loop():
                loop.run_forever()
            threading.Thread(target=run_loop, daemon=True).start()

        async def start_operations():
            if not self._client or not self._client.is_connected:
                try:
                    await self.connect()
                except Exception as e:
                    self._task_state = -1
                    print(f"连接失败: {e}")
                    return

            if self._task_state == 0:
                self._stop_event.clear()
                self._task = asyncio.create_task(self._run_task(loop_ms))

        asyncio.run_coroutine_threadsafe(start_operations(), loop)

    def set_data_update_callback(self, callback: Callable[[float, str, str], None]):
        """设置数据更新回调 (data, unit, mode)"""
        self._data_update_callback = callback

    async def _run_task(self, loop_ms=1000):
        """后台任务主循环"""
        self._task_state = 1
        while not self._stop_event.is_set():
            try:
                data, unit, mode = await self.get_data()
                if data is not None:
                    self._current_data = data
                    self._current_unit = unit
                    self._current_mode = mode
                    if self._data_update_callback:
                        self._data_update_callback(data, unit, mode)
                await asyncio.sleep(loop_ms/1000)
            except Exception as e:
                print(f"任务运行错误: {e}")
                self._task_state = -1
                await asyncio.sleep(1)
                return
        await self.disconnect()
        self._task_state = 0

    def stop(self):
        """停止后台任务"""
        if self._task:
            self._stop_event.set()
            while self._task_state == 1:
                time.sleep(0.1)
        self._task_state = 0

    def get_current_data(self) -> Tuple[Optional[float], str, str]:
        """获取最新数据 (value, unit, mode)"""
        return self._current_data, self._current_unit, self._current_mode

    async def connect(self) -> bool:
        """连接蓝牙设备"""
        retry_count = 0
        while retry_count < self.max_retry:
            try:
                device = await BleakScanner.find_device_by_address(self._device_addr)
                if not device:
                    raise Exception(f"未找到设备: {self._device_addr}")

                print(f"找到设备: {self._device_addr}")
                self._client = BleakClient(device)
                print("开始连接:{}".format(self._device_addr))
                await self._client.connect()
                print("连接成功:{}".format(self._device_addr))

                for service in self._client.services:
                    for char in service.characteristics:
                        if self.read_uuid == char.uuid:
                            self._rx_char = char
                        if self.write_uuid == char.uuid:
                            self._tx_char = char

                if not self._rx_char or not self._tx_char:
                    raise Exception("未找到所需的特征值")

                print("设置通知:{}".format(self._rx_char.uuid))
                await self._client.start_notify(self._rx_char.uuid, self._notification_handler)
                return True
            except Exception as e:
                retry_count += 1
                print(f"连接失败 (尝试 {retry_count}/{self.max_retry}): {e}")
                if retry_count < self.max_retry:
                    await asyncio.sleep(2)
        raise Exception("达到最大重试次数，连接失败")

    async def disconnect(self):
        """断开蓝牙连接"""
        if self._client and self._client.is_connected:
            await self._client.stop_notify(self._rx_char.uuid)
            await self._client.disconnect()

    def _notification_handler(self, sender: BleakGATTCharacteristic, data: bytearray):
        """接收数据回调函数"""
        self._response_data.extend(data)
        self._response_event.set()

    async def send_command(self, cmd: bytes, timeout: float = 1.0) -> Optional[bytearray]:
        """发送命令并等待响应"""
        if not self._client or not self._client.is_connected:
            raise Exception("设备未连接")

        self._response_data.clear()
        self._response_event.clear()

        await self._client.write_gatt_char(self._tx_char.uuid, cmd)

        try:
            await asyncio.wait_for(self._response_event.wait(), timeout)
            return self._response_data
        except asyncio.TimeoutError:
            print("等待响应超时")
            return None

    def _calculate_checksum(self, cmd_bytes: list) -> int:
        """计算校验和 (简单的异或校验)"""
        checksum = 0
        for b in cmd_bytes[:-1]:  # 排除最后一个字节（校验位本身）
            checksum ^= b
        return checksum

    # ==================== 测量模式设置 ====================

    async def set_dc_voltage_mode(self) -> bool:
        """设置直流电压模式 (DCV)"""
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x30, 0x12])
        response = await self.send_command(cmd)
        print(f"设置直流电压模式: {'成功' if response else '失败'}")
        return response is not None

    async def set_ac_voltage_mode(self) -> bool:
        """设置交流电压模式 (ACV)"""
        # 根据协议推测，AC模式可能在第5字节使用不同的值
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x31, 0x13])
        response = await self.send_command(cmd)
        print(f"设置交流电压模式: {'成功' if response else '失败'}")
        return response is not None

    async def set_dc_current_mode(self) -> bool:
        """设置直流电流模式 (DCA)"""
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x39, 0x09])
        response = await self.send_command(cmd)
        print(f"设置直流电流模式: {'成功' if response else '失败'}")
        return response is not None

    async def set_ac_current_mode(self) -> bool:
        """设置交流电流模式 (ACA)"""
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x3a, 0x08])
        response = await self.send_command(cmd)
        print(f"设置交流电流模式: {'成功' if response else '失败'}")
        return response is not None

    async def set_resistance_mode(self) -> bool:
        """设置电阻模式 (Ω)"""
        # 0x32 可能对应电阻模式
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x32, 0x1b])
        response = await self.send_command(cmd)
        print(f"设置电阻模式: {'成功' if response else '失败'}")
        return response is not None

    async def set_capacitance_mode(self) -> bool:
        """设置电容模式 (F)"""
        # 0x33 可能对应电容模式
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x33, 0x1a])
        response = await self.send_command(cmd)
        print(f"设置电容模式: {'成功' if response else '失败'}")
        return response is not None

    async def set_frequency_mode(self) -> bool:
        """设置频率模式 (Hz)"""
        # 0x34 可能对应频率模式
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x34, 0x19])
        response = await self.send_command(cmd)
        print(f"设置频率模式: {'成功' if response else '失败'}")
        return response is not None

    async def set_temperature_mode(self) -> bool:
        """设置温度模式 (°C)"""
        # 0x35 可能对应温度模式
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x35, 0x18])
        response = await self.send_command(cmd)
        print(f"设置温度模式: {'成功' if response else '失败'}")
        return response is not None

    async def set_diode_mode(self) -> bool:
        """设置二极管模式"""
        # 0x36 可能对应二极管模式
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x36, 0x1f])
        response = await self.send_command(cmd)
        print(f"设置二极管模式: {'成功' if response else '失败'}")
        return response is not None

    async def set_continuity_mode(self) -> bool:
        """设置通断模式"""
        # 0x37 可能对应通断模式
        cmd = bytes([0xaf, 0x05, 0x03, 0x06, 0x01, 0x37, 0x1e])
        response = await self.send_command(cmd)
        print(f"设置通断模式: {'成功' if response else '失败'}")
        return response is not None

    # ==================== 向后兼容 ====================

    async def set_voltage_mode(self) -> bool:
        """设置电压模式（默认直流，兼容旧代码）"""
        return await self.set_dc_voltage_mode()

    async def set_current_mode(self) -> bool:
        """设置电流模式（默认直流，兼容旧代码）"""
        return await self.set_dc_current_mode()

    # ==================== 数据获取 ====================

    async def get_data(self) -> Tuple[Optional[float], str, str]:
        """
        获取测量数据
        返回: (value, unit, mode)
        """
        cmd = bytes([0xaf, 0x05, 0x03, 0x09, 0x00, 0x40])
        response = await self.send_command(cmd)

        if response is not None and len(response) >= 6:
            # 解析比例因子
            if response[-8] == 0x18:
                data_x = 0.1
            elif response[-8] == 0x19:
                data_x = -0.1
            elif response[-8] == 0x16:
                data_x = 1
            elif response[-8] == 0x17:
                data_x = -1
            elif response[-8] == 0x15:
                data_x = -0.01
            elif response[-8] == 0x14:
                data_x = 0.01
            elif response[-8] == 0x28:
                data_x = 0.1
            elif response[-8] == 0x29:
                data_x = -0.1
            else:
                data_x = 1

            # 解码单位和模式
            mode_byte = response[5]
            if mode_byte == 0x30:
                unit, mode = 'mV', 'DC Voltage'
            elif mode_byte == 0x31:
                unit, mode = 'mV', 'AC Voltage'
            elif mode_byte == 0x39:
                unit, mode = 'mA', 'DC Current'
            elif mode_byte == 0x3a:
                unit, mode = 'mA', 'AC Current'
            elif mode_byte == 0x32:
                unit, mode = 'Ω', 'Resistance'
            elif mode_byte == 0x33:
                unit, mode = 'nF', 'Capacitance'
            elif mode_byte == 0x34:
                unit, mode = 'Hz', 'Frequency'
            elif mode_byte == 0x35:
                unit, mode = '°C', 'Temperature'
            elif mode_byte == 0x36:
                unit, mode = 'V', 'Diode'
            elif mode_byte == 0x37:
                unit, mode = 'Ω', 'Continuity'
            else:
                unit, mode = f'0x{mode_byte:02x}', 'Unknown'

            # 解析数据值
            data = response[-3] | response[-2] << 8
            result = round(data * data_x, 2)
            return result, unit, mode

        return None, '', ''

    # ==================== 自定义命令 ====================

    async def send_custom_command(self, cmd_bytes: list) -> Tuple[Optional[bytearray], str]:
        """
        发送自定义命令用于实验和调试
        参数: cmd_bytes - 命令字节列表，例如 [0xaf, 0x05, 0x03, 0x06, 0x01, 0x30, 0x12]
        返回: (response, hex_string)
        """
        cmd = bytes(cmd_bytes)
        print(f"发送自定义命令: {cmd.hex()}")
        response = await self.send_command(cmd)
        if response:
            return response, response.hex()
        return None, ""

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()

    def set_mode(self, mode: int):
        """设置模式（兼容旧代码）"""
        self._mode = mode

    def get_state(self) -> int:
        """获取状态"""
        return self._task_state


if __name__ == "__main__":
    import time

    def update_display(data, unit, mode):
        print(f"[{mode}] 数据: {data} {unit}")

    device = Com_DM40A()
    device.set_data_update_callback(update_display)
    device.run(200)

    print("等待连接...")
    try:
        while device.get_state() != 1:
            if device.get_state() == -1:
                print("连接失败，退出")
                exit(1)
            time.sleep(0.5)

        print("连接成功！开始测试各测量模式...")
        print("\n=== DM40A 测量模式测试 ===\n")

        # 测试各种模式
        modes = [
            ("直流电压", device.set_dc_voltage_mode),
            ("交流电压", device.set_ac_voltage_mode),
            ("直流电流", device.set_dc_current_mode),
            ("交流电流", device.set_ac_current_mode),
            ("电阻", device.set_resistance_mode),
            ("电容", device.set_capacitance_mode),
            ("频率", device.set_frequency_mode),
            ("温度", device.set_temperature_mode),
            ("二极管", device.set_diode_mode),
            ("通断", device.set_continuity_mode),
        ]

        for name, mode_func in modes:
            print(f"\n--- 切换到 {name} 模式 ---")
            asyncio.run(mode_func())
            time.sleep(2)  # 等待数据稳定

        print("\n测试完成，继续读取数据...")

        # 持续读取数据
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n手动停止")
        device.stop()
        print("结束")
