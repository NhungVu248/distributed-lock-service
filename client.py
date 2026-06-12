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
        if mode == "timeout":
            demo_timeout()
        else:
            demo()
    except requests.exceptions.ConnectionError:
        print("Lỗi: Không kết nối được server. Hãy chạy 'python server.py' trước.")
        sys.exit(1)
