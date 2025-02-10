import cv2
import face_recognition
import numpy as np
import datetime
import csv
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import time

class FaceAttendanceSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_names = []
        self.attendance_file = "attendance.csv"
        self.initialize_system()
        self.setup_gui()

    def initialize_system(self):
        # สร้างโฟลเดอร์เก็บรูปภาพถ้ายังไม่มี
        Path("face_database").mkdir(exist_ok=True)
        
        # โหลดรูปภาพจากฐานข้อมูล
        for face_image in Path("face_database").glob("*.jpg"):
            image = face_recognition.load_image_file(str(face_image))
            encoding = face_recognition.face_encodings(image)[0]
            self.known_face_encodings.append(encoding)
            self.known_face_names.append(face_image.stem)

        # เพิ่มการตรวจสอบไฟล์ attendance.csv
        if not Path(self.attendance_file).exists():
            with open(self.attendance_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Name', 'Date', 'Time', 'Status'])
        
        # เพิ่มไฟล์ log
        self.log_file = "system_log.txt"
        self.log_message("System initialized")

        # เพิ่มตัวแปรสำหรับ caching
        self.face_cache = {}
        self.last_detection_time = {}
        self.detection_interval = 0.5  # ตรวจจับทุก 0.5 วินาที

    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("ระบบบันทึกเวลาด้วยใบหน้า")
        self.root.geometry("800x600")

        # สร้างเฟรมหลัก
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # สร้างปุ่มต่างๆ
        ttk.Label(main_frame, text="ระบบบันทึกเวลาด้วยใบหน้า", font=('TH Sarabun New', 20, 'bold')).grid(row=0, column=0, columnspan=2, pady=20)
        
        ttk.Button(main_frame, text="ลงทะเบียนใบหน้าใหม่", command=self.show_register_dialog).grid(row=1, column=0, columnspan=2, pady=10, padx=10, sticky=tk.EW)
        ttk.Button(main_frame, text="เริ่มระบบบันทึกเวลา", command=self.run).grid(row=2, column=0, columnspan=2, pady=10, padx=10, sticky=tk.EW)
        ttk.Button(main_frame, text="ออกจากโปรแกรม", command=self.root.quit).grid(row=3, column=0, columnspan=2, pady=10, padx=10, sticky=tk.EW)

    def show_register_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("ลงทะเบียนใบหน้าใหม่")
        dialog.geometry("300x150")

        ttk.Label(dialog, text="กรุณาใส่ชื่อ:").grid(row=0, column=0, pady=20, padx=10)
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var)
        name_entry.grid(row=0, column=1, pady=20, padx=10)

        def start_registration():
            name = name_var.get()
            if name:
                dialog.destroy()
                self.register_new_face(name)
            else:
                messagebox.showerror("Error", "กรุณาใส่ชื่อ")

        ttk.Button(dialog, text="ลงทะเบียน", command=start_registration).grid(row=1, column=0, columnspan=2, pady=20)

    def register_new_face(self, name):
        cap = cv2.VideoCapture(0)
        
        register_window = tk.Toplevel(self.root)
        register_window.title("ถ่ายภาพใบหน้า")
        
        label = ttk.Label(register_window)
        label.pack()
        
        instruction_label = ttk.Label(register_window, text="กด 'S' เพื่อถ่ายภาพ หรือ 'Q' เพื่อยกเลิก")
        instruction_label.pack()

        # เพิ่มตัวแปรสำหรับเก็บสถานะการกดปุ่ม
        key_pressed = {'value': None}

        # เพิ่มฟังก์ชันจัดการการกดปุ่ม
        def on_key_press(event):
            if event.char.lower() == 's':
                key_pressed['value'] = 's'
            elif event.char.lower() == 'q':
                key_pressed['value'] = 'q'

        # ผูกการทำงานกับ event การกดปุ่ม
        register_window.bind('<Key>', on_key_press)

        def update_frame():
            ret, frame = cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame)
                imgtk = ImageTk.PhotoImage(image=img)
                label.imgtk = imgtk
                label.configure(image=imgtk)
                
                # ตรวจสอบการกดปุ่มจากตัวแปร key_pressed
                if key_pressed['value'] == 's':
                    cv2.imwrite(f"face_database/{name}.jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                    image = face_recognition.load_image_file(f"face_database/{name}.jpg")
                    encoding = face_recognition.face_encodings(image)[0]
                    self.known_face_encodings.append(encoding)
                    self.known_face_names.append(name)
                    messagebox.showinfo("สำเร็จ", "ลงทะเบียนใบหน้าเรียบร้อยแล้ว")
                    register_window.destroy()
                    cap.release()
                    return
                elif key_pressed['value'] == 'q':
                    register_window.destroy()
                    cap.release()
                    return
                
                register_window.after(10, update_frame)
            
        update_frame()

    def mark_attendance(self, name):
        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        
        with open(self.attendance_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([name, date, time])

    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")

    def run(self):
        attendance_window = tk.Toplevel(self.root)
        attendance_window.title("ระบบบันทึกเวลา")

        # Remove these erroneous lines that seem to be accidentally added
        # query = query
        # query.prot_name_la[0]
        
        # Add window size and make it resizable
        attendance_window.geometry("800x800")
        attendance_window.resizable(True, True)
        
        # สร้าง frame สำหรับวิดีโอและตาราง
        video_frame = ttk.Frame(attendance_window)
        video_frame.pack(side=tk.LEFT, padx=10, pady=10)
        
        table_frame = ttk.Frame(attendance_window)
        table_frame.pack(side=tk.RIGHT, padx=10, pady=10)
        
        video_label = ttk.Label(video_frame)
        video_label.pack()

        # สร้างตารางแสดงผล
        columns = ('ชื่อ', 'เวลา')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings')
        
        # กำหนดหัวข้อคอลัมน์
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        tree.pack(pady=10)
        
        # สร้าง Label สำหรับแสดงสถานะ
        status_label = ttk.Label(table_frame, text="สถานะ: กำลังตรวจจับใบหน้า", font=('TH Sarabun New', 12))
        status_label.pack(pady=5)
        
        cap = cv2.VideoCapture(0)
        
        # เก็บรายชื่อที่ตรวจจับได้เพื่อไม่ให้ซ้ำในตาราง
        detected_names = set()

        def update_frame():
            ret, frame = cap.read()
            if ret:
                # ลดขนาดเฟรมลงเพื่อเพิ่มความเร็ว
                frame_small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(frame_small, cv2.COLOR_BGR2RGB)

                # ตรวจจับใบหน้าเป็นช่วงเวลา
                current_time = time.time()
                process_this_frame = True
                
                for name in self.last_detection_time:
                    if current_time - self.last_detection_time[name] < self.detection_interval:
                        process_this_frame = False
                        break

                if process_this_frame:
                    try:
                        # ใช้ model "hog" แทน "cnn" เพื่อความเร็ว
                        face_locations = face_recognition.face_locations(rgb_small_frame, model="hog")
                        
                        if face_locations:
                            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                            # ใช้ numpy vectorization แทน loop
                            if len(self.known_face_encodings) > 0:
                                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encodings[0])
                                best_match_indices = np.where(face_distances < 0.45)[0]

                                for idx in best_match_indices:
                                    name = self.known_face_names[idx]
                                    self.last_detection_time[name] = current_time
                                    
                                    # ขยายพิกัดกลับไปขนาดเดิม
                                    top, right, bottom, left = [coord * 4 for coord in face_locations[0]]
                                    
                                    # วาดกรอบและข้อความ
                                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                                    cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    except Exception as e:
                        self.log_message(f"Error in face detection: {str(e)}")

                # แปลงเฟรมเพื่อแสดงผล
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(frame_rgb)
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.imgtk = imgtk
                video_label.configure(image=imgtk)

            attendance_window.after(10, update_frame)

        # Add cleanup handler
        def on_closing():
            cap.release()
            attendance_window.destroy()
            
        attendance_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        # เพิ่มปุ่มดูประวัติการเข้างาน
        ttk.Button(table_frame, text="ดูประวัติการเข้างาน", 
                  command=self.show_attendance_history).pack(pady=5)
        
        update_frame()

    def show_attendance_history(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("ประวัติการเข้างาน")
        history_window.geometry("600x400")

        # สร้างตารางแสดงประวัติ
        columns = ('ชื่อ', 'วันที่', 'เวลา', 'สถานะ')
        tree = ttk.Treeview(history_window, columns=columns, show='headings')
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=140)

        # โหลดข้อมูลจากไฟล์ CSV
        with open(self.attendance_file, 'r') as f:
            reader = csv.reader(f)
            next(reader)  # ข้ามส่วนหัว
            for row in reader:
                tree.insert('', 0, values=row)

        tree.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

if __name__ == "__main__":
    system = FaceAttendanceSystem()
    system.root.mainloop()
