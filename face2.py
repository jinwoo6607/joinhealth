
import pandas as pd
import cv2
import face_recognition
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
import numpy as np

# CSV 파일 초기화 (회원정보 저장)
columns = ['Name', 'Birth Date', 'Phone', 'Goal', 'Join Date', 'Face Encoding']
df = pd.DataFrame(columns=columns)

# 출석 데이터 파일
attendance_columns = ['Name', 'Join Date', 'Exit Date']
attendance_df = pd.DataFrame(columns=attendance_columns)

# 회원 얼굴 인식에 사용할 이미지 파일 경로
face_encodings = {}

# 웹캠 상태 점검 함수
def check_webcam():
    cap = cv2.VideoCapture(0)  # 0번 장치를 기본 웹캠으로 열기

    if not cap.isOpened():
        messagebox.showerror("웹캠 오류", "웹캠을 열 수 없습니다. 웹캠이 다른 프로그램에서 사용 중일 수 있습니다.")
        cap.release()
        return False

    ret, frame = cap.read()
    if not ret:
        messagebox.showerror("캡처 오류", "웹캠에서 프레임을 캡처할 수 없습니다. 웹캠이 정상적으로 작동하지 않습니다.")
        cap.release()
        return False

    cap.release()  # 웹캠 리소스를 해제
    return True  # 웹캠이 정상적으로 작동하는 경우

# 회원 정보 입력 받기
def get_member_input():
    def on_submit():
        name = name_entry.get()
        birth_date = birth_entry.get()
        phone = phone_entry.get()
        goal = goal_entry.get()
        join_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # 웹캠 상태 점검
        if not check_webcam():
            return

        # 웹캠에서 얼굴 이미지 캡처
        cap = cv2.VideoCapture(0)
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("웹캠 오류", "웹캠을 열 수 없습니다.")
            return

        # 얼굴 인식
        rgb_frame = frame[:, :, ::-1]  # OpenCV는 BGR 형식, face_recognition은 RGB 형식
        face_locations = face_recognition.face_locations(rgb_frame)

        if len(face_locations) == 0:
            messagebox.showerror("얼굴 인식 오류", "얼굴을 인식할 수 없습니다.")
            cap.release()
            return

        # 얼굴 인코딩
        face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]
        face_encodings[name] = face_encoding  # 회원 이름과 얼굴 인코딩을 매핑

        # 회원 정보를 DataFrame에 저장
        new_member = pd.DataFrame([{
            'Name': name,
            'Birth Date': birth_date,
            'Phone': phone,
            'Goal': goal,
            'Join Date': join_date,
            'Face Encoding': face_encoding.tolist()  # 얼굴 인코딩을 리스트로 저장
        }])

        # 기존 데이터와 합치기
        global df
        df = pd.concat([df, new_member], ignore_index=True)
        df.to_csv('members.csv', index=False)  # CSV에 저장
        messagebox.showinfo("회원 등록", "회원이 등록되었습니다.")
        cap.release()  # 웹캠 종료
        root.quit()  # 창 닫기

    # 회원 정보를 받는 창 만들기
    root = tk.Tk()
    root.title("회원 정보 입력")

    # 라벨과 입력란 추가
    tk.Label(root, text="이름").pack()
    name_entry = tk.Entry(root)
    name_entry.pack()

    tk.Label(root, text="생년월일 (YYYY-MM-DD)").pack()
    birth_entry = tk.Entry(root)
    birth_entry.pack()

    tk.Label(root, text="전화번호").pack()
    phone_entry = tk.Entry(root)
    phone_entry.pack()

    tk.Label(root, text="운동 목표").pack()
    goal_entry = tk.Entry(root)
    goal_entry.pack()

    # 제출 버튼
    submit_button = tk.Button(root, text="제출", command=on_submit)
    submit_button.pack()

    root.mainloop()

# 얼굴 인식으로 회원 자동 확인
def auto_identify_member():
    if not check_webcam():
        return

    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if not ret:
        print("웹캠을 열 수 없습니다.")
        cap.release()
        return

    # 얼굴 인식: BGR을 RGB로 변환
    rgb_frame = frame[:, :, ::-1]  # OpenCV는 BGR 형식, face_recognition은 RGB 형식
    face_locations = face_recognition.face_locations(rgb_frame)

    if len(face_locations) == 0:
        print("얼굴을 인식할 수 없습니다.")
        cap.release()
        return

    print(f"얼굴 위치: {face_locations}")  # 얼굴 위치 출력하여 디버깅
    
    # 얼굴 인코딩
    face_encoding = face_recognition.face_encodings(rgb_frame, face_locations)[0]

    # 등록된 회원과 비교
    matches = face_recognition.compare_faces(list(face_encodings.values()), face_encoding)

    if True in matches:
        match_index = matches.index(True)
        name = list(face_encodings.keys())[match_index]
        print(f"인식된 회원: {name}")
        cap.release()  # 웹캠 종료
        return name
    else:
        print("회원이 인식되지 않았습니다.")
        cap.release()
        return None

# 출석 관리: 출석 기록
def record_attendance(name):
    join_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    attendance_data = pd.DataFrame([{
        'Name': name,
        'Join Date': join_date,
        'Exit Date': None
    }])
    global attendance_df
    attendance_df = pd.concat([attendance_df, attendance_data], ignore_index=True)
    attendance_df.to_csv('attendance.csv', index=False)
    print(f"{name} 입장 기록됨")

# 출석 관리: 퇴장 기록
def record_exit(name):
    exit_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    attendance_df.loc[attendance_df['Name'] == name, 'Exit Date'] = exit_date
    attendance_df.to_csv('attendance.csv', index=False)
    print(f"{name} 퇴장 기록됨")

# 관리자 화면 (회원 수정 및 삭제)
def admin_menu():
    while True:
        print("\n관리자 메뉴:")
        print("1. 회원 정보 수정")
        print("2. 회원 정보 삭제")
        print("3. 종료")
        choice = input("원하는 작업을 선택하세요: ")

        if choice == "1":
            name = input("수정할 회원의 이름을 입력하세요: ")
            modify_member(name)
        elif choice == "2":
            name = input("삭제할 회원의 이름을 입력하세요: ")
            delete_member(name)
        elif choice == "3":
            break
        else:
            print("잘못된 선택입니다.")

# 메인 프로그램
def main():
    while True:
        print("\n메인 메뉴:")
        print("1. 회원 등록")
        print("2. 얼굴 인식으로 자동 회원 확인")
        print("3. 출석 기록")
        print("4. 출석 퇴장 기록")
        print("5. 관리자 메뉴")
        print("6. 종료")
        choice = input("원하는 작업을 선택하세요: ")

        if choice == "1":
            get_member_input()
        elif choice == "2":
            name = auto_identify_member()
            if name:
                record_attendance(name)
        elif choice == "3":
            name = input("입장할 회원 이름을 입력하세요: ")
            record_attendance(name)
        elif choice == "4":
            name = input("퇴장할 회원 이름을 입력하세요: ")
            record_exit(name)
        elif choice == "5":
            admin_menu()
        elif choice == "6":
            print("프로그램을 종료합니다.")
            break
        else:
            print("잘못된 선택입니다.")

if __name__ == "__main__":
    main()
