import requests
import json
import sys
import time

BASE_URL = "http://localhost:5000"


def lock(client_id, resource, ttl=30, wait=False):
    response = requests.post(f"{BASE_URL}/lock", json={
        "client_id": client_id,
        "resource": resource,
        "ttl": ttl,
        "wait": wait
    })
    return response.json()


def unlock(client_id, resource):
    response = requests.post(f"{BASE_URL}/unlock", json={
        "client_id": client_id,
        "resource": resource
    })
    return response.json()


def status(resource):
    response = requests.get(f"{BASE_URL}/status/{resource}")
    return response.json()


def get_locks():
    response = requests.get(f"{BASE_URL}/locks")
    return response.json()


def renew(client_id, resource, ttl=30):
    response = requests.post(f"{BASE_URL}/renew", json={
        "client_id": client_id,
        "resource": resource,
        "ttl": ttl
    })
    return response.json()


def get_queue(resource):
    response = requests.get(f"{BASE_URL}/queue/{resource}")
    return response.json()


def get_logs():
    response = requests.get(f"{BASE_URL}/logs")
    return response.json()


def show(label, result):
    status = "OK" if result.get("success") else "FAIL"
    print(f"[{status}] {label}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print()


def demo():
    print("=" * 50)
    print("  Demo Giai đoạn 2: Basic Lock / Unlock")
    print("=" * 50)
    print()

    # 1. Client A lock file_A thành công
    show("client_A xin khóa file_A", lock("client_A", "file_A", ttl=30))

    # 2. Client B lock file_A bị từ chối
    show("client_B xin khóa file_A (bị từ chối)", lock("client_B", "file_A", ttl=30))

    # 3. Client A unlock file_A thành công
    show("client_A nhả khóa file_A", unlock("client_A", "file_A"))

    # 4. Client B lock file_A thành công sau khi A unlock
    show("client_B xin khóa file_A (sau khi A unlock)", lock("client_B", "file_A", ttl=30))


def demo_status():
    print("=" * 50)
    print("  Demo Giai đoạn 4: Lock Status / Monitoring")
    print("=" * 50)
    print()

    # 1. Lock file_A
    show("client_A xin khóa file_A (TTL=5s)", lock("client_A", "file_A", ttl=5))

    # 2. Xem status -> LOCKED
    show("GET /status/file_A (đang bị khóa)", status("file_A"))

    # 3. Xem danh sách tất cả lock
    show("GET /locks (danh sách lock hiện tại)", get_locks())

    # 4. Chờ hết TTL
    print("Chờ 6 giây cho lock hết hạn...\n")
    time.sleep(6)

    # 5. Xem status sau khi hết TTL -> FREE
    show("GET /status/file_A (sau khi hết hạn)", status("file_A"))

    # 6. Xem /locks sau khi hết TTL -> rỗng
    show("GET /locks (sau khi hết hạn)", get_locks())


def demo_queue():
    print("=" * 50)
    print("  Demo Giai đoạn 7: Waiting Queue")
    print("=" * 50)
    print()

    # 1. A lock file_A thành công
    show("client_A xin khóa file_A", lock("client_A", "file_A", ttl=30))

    # 2. B và C vào hàng đợi
    show("client_B xin khóa file_A với wait=True (vào queue)", lock("client_B", "file_A", wait=True))
    show("client_C xin khóa file_A với wait=True (vào queue)", lock("client_C", "file_A", wait=True))

    # 3. Xem hàng đợi
    show("GET /queue/file_A", get_queue("file_A"))

    # 4. A unlock → B tự động được cấp lock
    show("client_A nhả khóa file_A", unlock("client_A", "file_A"))

    # 5. Kiểm tra B đã có lock, C vẫn trong queue
    show("GET /status/file_A (B đang giữ)", status("file_A"))
    show("GET /queue/file_A (C vẫn chờ)", get_queue("file_A"))

    # 6. B unlock → C tự động được cấp lock
    show("client_B nhả khóa file_A", unlock("client_B", "file_A"))
    show("GET /status/file_A (C đang giữ)", status("file_A"))


def demo_renew():
    print("=" * 50)
    print("  Demo Giai đoạn 6: Renew Lock / Extend Lease")
    print("=" * 50)
    print()

    # 1. Client A lock file_A TTL=8s
    show("client_A xin khóa file_A (TTL=8s)", lock("client_A", "file_A", ttl=8))

    # 2. Client B lock → bị từ chối
    show("client_B xin khóa file_A (bị từ chối)", lock("client_B", "file_A"))

    # 3. Sau 5s, A renew thêm 30s
    print("Chờ 5 giây rồi client_A renew...\n")
    time.sleep(5)
    show("client_A gia hạn lock thêm 30s", renew("client_A", "file_A", ttl=30))

    # 4. Sau 5s nữa (đã qua TTL gốc 8s), lock vẫn còn
    print("Chờ thêm 5 giây (đã qua TTL gốc)...\n")
    time.sleep(5)
    show("GET /status/file_A (lock vẫn còn hiệu lực)", status("file_A"))

    # 5. Client B vẫn chưa lock được
    show("client_B xin khóa file_A (vẫn bị từ chối)", lock("client_B", "file_A"))

    # 6. Test: client không phải owner không được renew
    show("client_B cố gia hạn lock của A (bị từ chối)", renew("client_B", "file_A", ttl=30))


def demo_logs():
    print("=" * 50)
    print("  Demo Giai đoạn 5: Operation Logs")
    print("=" * 50)
    print()

    # Tạo ra các thao tác để có log
    lock("client_A", "file_A", ttl=30)
    lock("client_B", "file_A", ttl=30)          # bị từ chối
    lock("client_C", "file_A", ttl=30, wait=True)  # vào queue
    unlock("client_A", "file_A")                # A unlock, C auto-grant
    unlock("client_C", "file_A")

    # Hiển thị toàn bộ log
    result = get_logs()
    print(f"Tổng số log: {len(result['logs'])}\n")
    for entry in result["logs"]:
        print(f"  [{entry['result']:10}] {entry['time']}  "
              f"{entry['client_id']:10} {entry['action']:12} {entry['resource']}  "
              f"— {entry['message']}")
    print()


def demo_timeout():
    print("=" * 50)
    print("  Demo Giai đoạn 3: Lock Timeout / Lease Expiration")
    print("=" * 50)
    print()

    # 1. Client A lock file_B TTL 5 giây
    show("client_A xin khóa file_B (TTL=5s)", lock("client_A", "file_B", ttl=5))

    # 2. Client B lock ngay lập tức → thất bại
    show("client_B xin khóa file_B ngay lập tức (bị từ chối)", lock("client_B", "file_B", ttl=30))

    # 3. Chờ hết TTL
    print("Chờ 6 giây cho lock hết hạn...\n")
    time.sleep(6)

    # 4. Client B lock sau khi hết TTL → thành công
    show("client_B xin khóa file_B sau khi hết hạn (thành công)", lock("client_B", "file_B", ttl=30))


if __name__ == '__main__':
    try:
        mode = sys.argv[1] if len(sys.argv) > 1 else "basic"
        if mode == "queue":
            demo_queue()
        elif mode == "timeout":
            demo_timeout()
        elif mode == "status":
            demo_status()
        elif mode == "renew":
            demo_renew()
        elif mode == "logs":
            demo_logs()
        else:
            demo()
    except requests.exceptions.ConnectionError:
        print("Lỗi: Không kết nối được server. Hãy chạy 'python server.py' trước.")
        sys.exit(1)
