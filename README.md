# Distributed Lock Service (Mô phỏng)

Mô phỏng một **Distributed Lock Service** (dịch vụ khóa phân tán) gồm nhiều client cùng
gửi yêu cầu đến một **Lock Server** để xin khóa, nhả khóa và theo dõi trạng thái khóa của
tài nguyên dùng chung.

> Đề tài tham khảo ý tưởng từ **Google Chubby** — dịch vụ khóa phân tán nổi tiếng.

## Mục tiêu

Mô phỏng các vấn đề kinh điển trong hệ phân tán:

- **Loại trừ lẫn nhau (Mutual Exclusion):** một tài nguyên tại một thời điểm chỉ có một client giữ khóa.
- **Đồng bộ hóa:** server kiểm soát trạng thái lock để tránh xung đột khi nhiều client truy cập đồng thời.
- **Xử lý lỗi cơ bản:** lock tự hết hạn (lease/TTL) nếu client giữ quá lâu.
- **Hàng đợi (Waiting Queue):** client chờ đến lượt được cấp khóa.
- **Giám sát & Quản trị:** xem trạng thái lock, owner, thời gian còn lại; admin có thể cưỡng chế mở khóa.

## Chức năng

| Mã | Chức năng | Mức độ |
|-----|-----------|--------|
| F01 | Acquire Lock — Xin khóa tài nguyên | Bắt buộc |
| F02 | Release Lock — Nhả khóa | Bắt buộc |
| F03 | Lock Timeout / Lease Expiration | Bắt buộc |
| F04 | Lock Status / Monitoring | Bắt buộc |
| F05 | Operation Logs — Ghi log thao tác | Bắt buộc |
| F06 | Renew Lock — Gia hạn khóa | Mở rộng |
| F07 | Waiting Queue — Hàng đợi chờ khóa | Mở rộng |
| F08 | Force Unlock by Admin | Mở rộng |
| F09 | Multi-client Simulation | Mở rộng |

## Kiến trúc tổng quát

```
Client 1 ─┐
Client 2 ─┼──> Lock Server ───> Lock Manager
Client 3 ─┘                       ├──> Lock Status / Monitoring
                                  ├──> Waiting Queue
                                  └──> Operation Logs
```

## Công nghệ sử dụng

| Thành phần | Công nghệ |
|------------|-----------|
| Ngôn ngữ | Python |
| Framework API | Flask |
| Client demo | Python `requests` |
| Lưu trạng thái lock | Dictionary trong RAM |
| Hàng đợi | List / Queue trong Python |
| Kiểm thử API | Postman + terminal |
| Quản lý mã nguồn | GitHub |
| Môi trường chạy | Localhost, nhiều terminal |

## Cấu trúc thư mục

```
distributed-lock-service/
├── server.py              # Flask server, định nghĩa API
├── lock_manager.py        # Logic lock, unlock, timeout, queue
├── client.py              # Client gửi request thủ công
├── simulate_clients.py    # Mô phỏng nhiều client tranh khóa
├── requirements.txt       # Thư viện cần cài
├── README.md
├── docs/
│   ├── project_overview.md   # Lý thuyết Distributed Lock Service
│   ├── setup_guide.md        # Hướng dẫn cài đặt & chạy
│   ├── api_design.md         # Mô tả API
│   ├── test_cases.md         # Test case
│   └── screenshots/          # Ảnh kết quả thực nghiệm
└── report/
    ├── bao_cao.md            # Nội dung báo cáo
    └── slides/               # Slide trình bày
```

## Cài đặt

```bash
# 1. Clone repo
git clone <URL_REPO>
cd distributed-lock-service

# 2. (Khuyến nghị) Tạo môi trường ảo
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS / Linux:
source venv/bin/activate

# 3. Cài thư viện
pip install -r requirements.txt
```

## Chạy thử

> *Phần này sẽ được bổ sung từ Giai đoạn 2 trở đi, khi đã có `server.py` và `client.py`.*

```bash
# Chạy Lock Server
python server.py

# Mở terminal khác, chạy client
python client.py
```

## Thành viên nhóm

| STT | Họ tên | Vai trò / Phân công |
|-----|--------|---------------------|
| 1 | *(điền tên)* | *(ví dụ: Lock Manager logic)* |
| 2 | *(điền tên)* | *(ví dụ: API & Server)* |
| 3 | *(điền tên)* | *(ví dụ: Client & Simulation)* |

## Tài liệu

- [Tổng quan lý thuyết](docs/project_overview.md)
- [Hướng dẫn cài đặt](docs/setup_guide.md)
- [Thiết kế API](docs/api_design.md)
- [Test cases](docs/test_cases.md)
