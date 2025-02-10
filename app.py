import cv2
import face_recognition
import numpy as np
import datetime
import csv
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

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
                # ปรับขนาดเฟรมให้เหมาะสมเพื่อการประมวลผลที่เร็วขึ้น
                frame_height, frame_width = frame.shape[:2]
                if frame_width > 1000:
                    scale = 1000 / frame_width
                    frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)

                # แปลงสีให้ถูกต้องสำหรับการตรวจจับใบหน้า
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                try:
                    # ใช้ model CNN สำหรับความแม่นยำที่ดีกว่า (ถ้าเครื่องมีกำลังประมวลผลพอ)
                    face_locations = face_recognition.face_locations(rgb_frame, model="hog", number_of_times_to_upsample=1)
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

                    # ล้างรายชื่อที่ตรวจจับได้ในแต่ละเฟรม
                    current_detected = set()

                    for face_encoding, face_location in zip(face_encodings, face_locations):
                        if len(self.known_face_encodings) > 0:
                            # คำนวณระยะห่างใบหน้าและใช้ค่า threshold ที่เข้มงวดขึ้น
                            face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                            best_match_index = np.argmin(face_distances)
                            
                            # ปรับค่า threshold ให้เข้มงวดขึ้นเพื่อความแม่นยำ
                            if face_distances[best_match_index] < 0.45:  # ลดจาก 0.5 เป็น 0.45
                                name = self.known_face_names[best_match_index]
                                current_detected.add(name)
                                
                                top, right, bottom, left = face_location
                                
                                # เพิ่มความสวยงามของการแสดงผล
                                # กรอบนอก
                                cv2.rectangle(frame, (left-3, top-3), (right+3, bottom+3), (0, 0, 255), 2)
                                # กรอบใน
                                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                                
                                # พื้นหลังสำหรับชื่อ
                                label_y = top - 25 if top - 25 > 15 else top + 10
                                cv2.rectangle(frame, (left-3, label_y-10), (right+3, label_y+10), (0, 255, 0), cv2.FILLED)
                                cv2.putText(frame, name, (left + 6, label_y+5), 
                                          cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)
                                
                                # อัพเดทสถานะและบันทึกการเข้างาน
                                if name not in detected_names:
                                    detected_names.add(name)
                                    current_time = datetime.datetime.now().strftime("%H:%M:%S")
                                    tree.insert('', 0, values=(name, current_time))
                                    self.mark_attendance(name)
                                    status_label.config(text=f"สถานะ: บันทึกเวลาสำหรับ {name} เรียบร้อย")
                            else:
                                # แสดงสถานะเมื่อเจอใบหน้าแต่ไม่ตรงกับฐานข้อมูล
                                status_label.config(text="สถานะ: พบใบหน้าที่ไม่อยู่ในระบบ")

                    if len(face_locations) == 0:
                        status_label.config(text="สถานะ: ไม่พบใบหน้า")

                    # แสดงจำนวนใบหน้าที่ตรวจพบ
                    cv2.putText(frame, f"พบใบหน้า: {len(face_locations)}", (10, 30), 
                              cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 0), 2)

                except Exception as e:
                    status_label.config(text=f"สถานะ: เกิดข้อผิดพลาด - {str(e)}")
                    print(f"Error in face detection: {str(e)}")

                # แสดงภาพใน GUI
                img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                imgtk = ImageTk.PhotoImage(image=img)
                video_label.imgtk = imgtk
                video_label.configure(image=imgtk)

            attendance_window.after(10, update_frame)

        # Add cleanup handler
        def on_closing():
            cap.release()
            attendance_window.destroy()
            
        attendance_window.protocol("WM_DELETE_WINDOW", on_closing)
        
        update_frame()

if __name__ == "__main__":
    system = FaceAttendanceSystem()
    system.root.mainloop()
