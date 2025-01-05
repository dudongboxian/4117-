import cv2
import threading
import time
from tkinter import Tk, Label, Button
from PIL import Image, ImageTk  # 用于将OpenCV图像转换为Tkinter格式
from datetime import datetime
import os

# 打开摄像头，尝试使用 DirectShow (Windows)
cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)

if not cap.isOpened():
    print("无法连接摄像头")
    exit()

# 强制设置 MJPEG 格式
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))  # 强制使用 MJPEG 编解码器

# 用于保存摄像头视频的编解码器
fourcc = cv2.VideoWriter_fourcc(*'XVID')

# 录制标志和锁
is_recording = False
lock = threading.Lock()

# 当前录制的视频文件名
current_filename = "camera_record_1.avi"
camera_video_writer = None

# 视频最大大小限制（1GB），单位字节
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1GB

# 创建Tkinter窗口
root = Tk()
root.title("摄像头录制")

# 显示摄像头视频流的标签
camera_label = Label(root)
camera_label.pack()

# 检查并创建新的视频写入器
def check_and_create_new_video_writer():
    global camera_video_writer, current_filename
    if camera_video_writer is None or os.path.getsize(current_filename) > MAX_FILE_SIZE:
        # 释放当前视频写入器
        if camera_video_writer is not None:
            camera_video_writer.release()

        # 创建新的文件名，避免覆盖前一个文件
        base_name, ext = os.path.splitext(current_filename)
        new_index = int(base_name.split('_')[-1]) + 1 if base_name.split('_')[-1].isdigit() else 1
        current_filename = f"{base_name.split('_')[0]}_{new_index}{ext}"

        # 创建新的 VideoWriter 实例
        camera_video_writer = cv2.VideoWriter(current_filename, fourcc, 20.0, (640, 480))
        print(f"开始录制新视频: {current_filename}")

# 更新摄像头帧并添加水印
def update_camera_frame():
    global camera_video_writer
    while True:
        ret, frame = cap.read()
        if not ret:
            print("无法读取摄像头帧")
            break

        # 在每一帧上添加日期和时间水印（绿色）
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # 获取当前时间
        font = cv2.FONT_HERSHEY_SIMPLEX
        cv2.putText(frame, current_time, (10, 30), font, 1, (0, 255, 0), 2, cv2.LINE_AA)  # 绿色水印

        # 显示摄像头视频流
        frame_resized = cv2.resize(frame, (640, 480))  # 调整为合适的大小显示

        # 转换为RGB格式并转换为Pillow图像
        img = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(image=img_pil)

        # 更新UI中的摄像头画面
        camera_label.configure(image=img_tk)
        camera_label.image = img_tk

        with lock:
            if is_recording:
                # 检查视频文件大小，超过1GB时创建新的文件
                check_and_create_new_video_writer()

                # 录制摄像头视频
                camera_video_writer.write(frame_resized)

        time.sleep(0.03)  # 控制帧率

# 开始录制
def start_recording():
    global is_recording
    with lock:
        if not is_recording:
            is_recording = True
            print("开始录制")
            start_button.config(state="disabled")
            stop_button.config(state="normal")

# 停止录制
def stop_recording():
    global is_recording, camera_video_writer
    with lock:
        if is_recording:
            is_recording = False
            if camera_video_writer is not None:
                camera_video_writer.release()  # 释放视频写入器
                camera_video_writer = None
            print("停止录制")
            start_button.config(state="normal")
            stop_button.config(state="disabled")

# 创建按钮来控制录制
start_button = Button(root, text="开始录制", command=start_recording)
start_button.pack()

stop_button = Button(root, text="停止录制", command=stop_recording, state="disabled")
stop_button.pack()

# 启动摄像头更新线程
camera_thread = threading.Thread(target=update_camera_frame, daemon=True)
camera_thread.start()

# 启动Tkinter主循环
root.mainloop()

# 释放资源
cap.release()
cv2.destroyAllWindows()
