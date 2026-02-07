import asyncio
import websockets
import json
import pyaudio
import numpy as np
import sys

# --- 配置参数 ---
ASR_URI = "ws://localhost:10095"
RATE = 16000
CHUNK_MS = 100  # 每 100ms 发送一次数据
CHUNK_SIZE = int(RATE * CHUNK_MS / 1000)

async def main():
    p = pyaudio.PyAudio()
    stream = None
    
    try:
        # 1. 尝试连接 ASR 服务
        async with websockets.connect(ASR_URI) as websocket:
            print("✅ 已连接到灵脑 ASR 服务")

            # 2. 发送握手配置 (必须在发音频前完成)
            config = {
                "mode": "2pass",
                "chunk_size": [5, 10, 5],
                "chunk_interval": 10,
                "wav_name": "mic",
                "is_speaking": True,
                "hotwords": "灵动 25"
            }
            await websocket.send(json.dumps(config))
            
            # 给服务端一点点初始化时间，防止数据包撞车
            await asyncio.sleep(0.3)

            # 3. 寻找并打开麦克风
            try:
                # 优先尝试单声道
                stream = p.open(format=pyaudio.paInt16, channels=1, rate=RATE, 
                                input=True, frames_per_buffer=CHUNK_SIZE)
                num_channels = 1
                print("🎤 麦克风已就绪 (单声道模式)")
            except:
                # 如果硬件只支持双声道，则强制开启双声道
                stream = p.open(format=pyaudio.paInt16, channels=2, rate=RATE, 
                                input=True, frames_per_buffer=CHUNK_SIZE)
                num_channels = 2
                print("🎤 麦克风已就绪 (双声道模式，已开启实时转换)")

            print("\n" + "="*50)
            print(">>> 灵脑正在听... 请说：‘灵动灵动，向前走’")
            print(">>> 提示：观察音量条，如果不跳动请检查alsamixer")
            print("="*50 + "\n")

            while True:
                # 读取音频
                raw_data = stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_np = np.frombuffer(raw_data, dtype=np.int16)

                # 如果是双声道，取左声道数据
                if num_channels == 2:
                    audio_np = audio_np[::2]
                
                # 计算音量条
                amplitude = np.abs(audio_np).max()
                level = int(amplitude / 800) # 灵敏度调节
                vol_bar = "█" * min(level, 20)
                
                # 发送二进制数据
                await websocket.send(audio_np.tobytes())

                # 非阻塞接收结果
                try:
                    res = await asyncio.wait_for(websocket.recv(), timeout=0.001)
                    res_dict = json.loads(res)
                    if "text" in res_dict and res_dict["text"].strip():
                        # 识别到文字，换行打印
                        print(f"\n[灵脑识别]: {res_dict['text']}")
                except asyncio.TimeoutError:
                    # 没结果时只刷新音量条
                    sys.stdout.write(f"\r[音量:{vol_bar:<20}]")
                    sys.stdout.flush()

    except ConnectionRefusedError:
        print("\n❌ 错误：无法连接到 ASR 服务。请确保 Docker 容器正在运行 (docker ps)")
    except KeyboardInterrupt:
        print("\n\n>>> 停止监听，正在关闭...")
    except Exception as e:
        print(f"\n❌ 发生意外错误: {e}")
    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()

if __name__ == "__main__":
    asyncio.run(main())