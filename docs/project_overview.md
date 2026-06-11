# Tổng quan lý thuyết: Distributed Lock Service

## 1. Vấn đề: Loại trừ lẫn nhau trong hệ phân tán

Trong một hệ thống chỉ có một tiến trình (single process), việc đảm bảo nhiều luồng (thread)
không cùng lúc sửa đổi một tài nguyên dùng chung khá đơn giản: ta dùng `mutex`, `semaphore`
hay `lock` trong ngôn ngữ lập trình.

Nhưng trong **hệ phân tán** (distributed system), các tiến trình chạy trên **nhiều máy khác
nhau**, không chia sẻ bộ nhớ chung, giao tiếp qua mạng. Lúc này các cơ chế khóa trong một máy
không còn dùng được nữa. Ta cần một cách để nhiều tiến trình trên nhiều máy **thống nhất** với
nhau rằng: *"tại một thời điểm, chỉ một tiến trình được phép truy cập tài nguyên X."*

Đây chính là bài toán **loại trừ lẫn nhau phân tán** (distributed mutual exclusion), và
**Distributed Lock Service** là một giải pháp phổ biến cho nó.

### Ví dụ thực tế

- Nhiều server cùng muốn ghi vào một file cấu hình → chỉ cho phép một server ghi tại một thời điểm.
- Bầu chọn **leader** (leader election): nhiều node tranh nhau giữ một khóa, node nào giữ được
  khóa thì trở thành leader.
- Đảm bảo một job định kỳ (cron job) chỉ chạy **đúng một lần** dù được triển khai trên nhiều máy.
- Tránh "double booking" khi nhiều người cùng đặt một chỗ ngồi / một phòng.

## 2. Distributed Lock Service là gì?

**Distributed Lock Service** là một dịch vụ trung tâm (hoặc một cụm máy chủ) cung cấp khả năng
**xin khóa (acquire)** và **nhả khóa (release)** trên các tài nguyên, để điều phối truy cập
giữa nhiều client phân tán.

Nguyên tắc cốt lõi:

1. Mọi client muốn truy cập tài nguyên đều phải **xin khóa trước** từ Lock Service.
2. Lock Service đảm bảo **tại một thời điểm chỉ một client giữ được khóa** của một tài nguyên.
3. Client dùng xong thì **nhả khóa** để client khác có cơ hội.

## 3. Cảm hứng từ Google Chubby

Đề tài này lấy ý tưởng từ **Chubby** — dịch vụ khóa phân tán do Google phát triển (Mike Burrows
mô tả trong bài báo năm 2006). Chubby được dùng nội bộ trong các hệ thống lớn của Google như
GFS và Bigtable, chủ yếu để **bầu chọn leader** và **lưu trữ cấu hình ít thay đổi**.

Một vài ý tưởng quan trọng từ Chubby mà dự án này mô phỏng lại (ở mức đơn giản):

| Ý tưởng từ Chubby | Cách dự án mô phỏng |
|-------------------|---------------------|
| Khóa được cấp cho một client tại một thời điểm | Lock Manager kiểm soát owner của mỗi tài nguyên |
| **Lease** — khóa có thời hạn, tự hết hạn nếu không gia hạn | Cơ chế **TTL** (`expires_at`) + tự giải phóng khi hết hạn |
| Client có thể gia hạn phiên giữ khóa | API **renew** để kéo dài TTL |
| Dịch vụ ghi lại sự kiện | Hệ thống **Operation Logs** |

> **Lưu ý phạm vi:** Chubby thật chạy trên một cụm máy chủ đồng bộ với nhau bằng thuật toán
> đồng thuận **Paxos** để chịu lỗi. Dự án của nhóm **không** mô phỏng phần đồng thuận này —
> ta dùng **một** Lock Server duy nhất để giữ bài toán ở mức vừa sức, tập trung làm rõ các khái
> niệm khóa, lease, hàng đợi và giám sát.

## 4. Các khái niệm cốt lõi

### 4.1. Lock & Owner
Mỗi tài nguyên (ví dụ `file_A`) có thể đang **FREE** (tự do) hoặc **LOCKED** (bị khóa). Khi
LOCKED, nó có một **owner** — chính là client đang giữ khóa.

### 4.2. Lease / TTL (Time To Live)
Khóa **không** được giữ vô thời hạn. Mỗi khóa có một **TTL** (số giây). Nếu hết thời gian mà
client không gia hạn, khóa **tự động hết hạn** và được giải phóng.

Đây là cơ chế **chống treo (deadlock prevention)** quan trọng: nếu một client xin khóa rồi
"chết" (crash hoặc mất mạng) mà không kịp nhả khóa, tài nguyên sẽ không bị khóa mãi mãi — nó
sẽ tự mở khi lease hết hạn.

### 4.3. Renew (gia hạn lease)
Nếu client cần giữ khóa lâu hơn dự kiến, nó **gia hạn** trước khi lease hết hạn để tiếp tục
giữ quyền sở hữu.

### 4.4. Waiting Queue (hàng đợi)
Khi một client xin khóa nhưng tài nguyên đang bận, thay vì bị từ chối ngay, nó có thể **xếp
hàng chờ**. Khi tài nguyên được giải phóng, client đầu hàng đợi sẽ **tự động được cấp khóa**
(auto-grant). Cách này giúp đảm bảo công bằng và tránh tình trạng client phải liên tục thử lại.

### 4.5. Force Unlock (admin cưỡng chế mở khóa)
Trong trường hợp đặc biệt (ví dụ một client bị treo và còn nhiều thời gian lease), **admin** có
quyền cưỡng chế mở khóa để giải phóng tài nguyên ngay.

### 4.6. Operation Logs (nhật ký thao tác)
Mọi thao tác (LOCK, UNLOCK, RENEW, EXPIRED, WAITING, AUTO_GRANT, FORCE_UNLOCK) đều được ghi
lại, phục vụ giám sát và gỡ lỗi.

## 5. Kiến trúc hệ thống của nhóm

```
Client 1 ─┐
Client 2 ─┼──> Lock Server (Flask API) ───> Lock Manager
Client 3 ─┘                                  ├──> locks         (dict trong RAM)
                                             ├──> waiting_queues (dict trong RAM)
                                             └──> logs           (list trong RAM)
```

| Thành phần | Vai trò |
|------------|---------|
| **Client** | Gửi yêu cầu lock / unlock / renew / status đến server |
| **Lock Server** | Nhận request qua REST API (Flask), gọi Lock Manager xử lý |
| **Lock Manager** | Toàn bộ logic: cấp khóa, nhả khóa, kiểm tra timeout, quản lý hàng đợi |
| **Waiting Queue** | Danh sách client đang chờ khóa từng tài nguyên |
| **Monitoring** | Hiển thị trạng thái khóa hiện tại |
| **Logs** | Ghi lại toàn bộ thao tác |
| **Admin** | Có quyền cưỡng chế mở khóa |

## 6. Những điều KHÔNG làm trong phạm vi đề tài

Để giữ dự án vừa sức và tránh sa đà, nhóm **không** triển khai:

- Thuật toán đồng thuận thật (Raft / Paxos) — quá khó, vượt phạm vi.
- Nhiều Lock Server đồng bộ dữ liệu với nhau — phức tạp về nhất quán dữ liệu.
- Cơ sở dữ liệu (database) — không cần thiết cho mô phỏng, dùng RAM là đủ.
- Giao diện web — tốn thời gian, không phải trọng tâm.
- Xác thực (authentication) đầy đủ — lệch khỏi mục tiêu chính.

## 7. Thuật ngữ tham khảo nhanh

| Thuật ngữ | Ý nghĩa |
|-----------|---------|
| Mutual Exclusion | Loại trừ lẫn nhau — chỉ một bên truy cập tại một thời điểm |
| Lease | Quyền giữ khóa có thời hạn |
| TTL (Time To Live) | Thời gian sống còn lại của khóa, tính bằng giây |
| Lease Expiration | Sự kiện khóa hết hạn và tự giải phóng |
| Deadlock | Tình trạng các bên chờ nhau vô tận, không ai tiến triển |
| Auto-grant | Tự động cấp khóa cho client đầu hàng đợi khi tài nguyên rảnh |

## 8. Tài liệu tham khảo

- Mike Burrows, *The Chubby lock service for loosely-coupled distributed systems*, Google, OSDI 2006.
- Apache **ZooKeeper** — một dịch vụ điều phối phân tán cũng cung cấp khóa.
- **etcd** — kho lưu trữ key-value phân tán, hỗ trợ khóa và bầu leader.
- Khái niệm **Redlock** của Redis — một cách triển khai khóa phân tán dựa trên Redis.
