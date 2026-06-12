import requests
import threading
import time
import sys

BASE_URL = "http://localhost:5000"
_print_lock = threading.Lock()


def log(client_id, event, resource, extra=""):
    suffix = f"  ({extra})" if extra else ""
    with _print_lock:
        print(f"  {client_id:12}: {event:20} {resource}{suffix}")


def do_lock(client_id, resource, ttl=30, wait=False, delay=0):
    time.sleep(delay)
    try:
        r = requests.post(f"{BASE_URL}/lock", json={
            "client_id": client_id, "resource": resource, "ttl": ttl, "wait": wait
        }, timeout=5).json()
        if r.get("success"):
            log(client_id, "LOCK_GRANTED", resource, f"TTL={ttl}s")
        elif r.get("queue_position"):
            log(client_id, "WAITING", resource, f"position={r['queue_position']}")
        else:
            log(client_id, "LOCK_DENIED", resource, r.get("message", ""))
        return r
    except Exception as e:
        log(client_id, "ERROR", resource, str(e))


def do_unlock(client_id, resource, delay=0):
    time.sleep(delay)
    try:
        r = requests.post(f"{BASE_URL}/unlock", json={
            "client_id": client_id, "resource": resource
        }, timeout=5).json()
        if r.get("success"):
            log(client_id, "UNLOCK_SUCCESS", resource)
        return r
    except Exception as e:
        log(client_id, "ERROR", resource, str(e))


def do_renew(client_id, resource, ttl=30, delay=0):
    time.sleep(delay)
    try:
        r = requests.post(f"{BASE_URL}/renew", json={
            "client_id": client_id, "resource": resource, "ttl": ttl
        }, timeout=5).json()
        if r.get("success"):
            log(client_id, "RENEW_SUCCESS", resource, f"new_expires={r.get('new_expires_at','')}")
        else:
            log(client_id, "RENEW_DENIED", resource, r.get("message", ""))
        return r
    except Exception as e:
        log(client_id, "ERROR", resource, str(e))


def do_force_unlock(admin_id, resource, delay=0):
    time.sleep(delay)
    try:
        r = requests.post(f"{BASE_URL}/admin/force-unlock", json={
            "admin_id": admin_id, "resource": resource
        }, timeout=5).json()
        if r.get("success"):
            log(admin_id, "FORCE_UNLOCK", resource)
        else:
            log(admin_id, "FORCE_UNLOCK_DENIED", resource, r.get("message", ""))
        return r
    except Exception as e:
        log(admin_id, "ERROR", resource, str(e))


def check_status(resource):
    try:
        r = requests.get(f"{BASE_URL}/status/{resource}", timeout=5).json()
        with _print_lock:
            owner = r.get("owner") or "FREE"
            ttl = r.get("ttl_remaining", 0)
            ql = r.get("queue_length", 0)
            print(f"  [STATUS] {resource}: {r['status']}  owner={owner}  "
                  f"ttl_remaining={ttl}s  queue={ql}")
    except Exception as e:
        print(f"  [STATUS ERROR] {e}")


def run_threads(tasks):
    threads = [threading.Thread(target=fn, args=args) for fn, args in tasks]
    for t in threads:
        t.start()
    for t in threads:
        t.join()


# ─── Kịch bản 1: Queue cơ bản ────────────────────────────────────────────────
def scenario_queue():
    print("\n" + "=" * 56)
    print("  Kịch bản 1: Queue cơ bản")
    print("  A lock → B, C chờ → A unlock → B auto-grant → C auto-grant")
    print("=" * 56)

    do_lock("client_A", "file_A", ttl=30)
    run_threads([
        (do_lock, ("client_B", "file_A", 30, True, 0.05)),
        (do_lock, ("client_C", "file_A", 30, True, 0.10)),
    ])

    time.sleep(0.2)
    check_status("file_A")

    do_unlock("client_A", "file_A")
    time.sleep(0.1)
    check_status("file_A")

    do_unlock("client_B", "file_A")
    time.sleep(0.1)
    check_status("file_A")

    do_unlock("client_C", "file_A")


# ─── Kịch bản 2: Lock Timeout ────────────────────────────────────────────────
def scenario_timeout():
    print("\n" + "=" * 56)
    print("  Kịch bản 2: Lock Timeout")
    print("  A lock TTL=4s → B chờ → A hết hạn → B auto-grant")
    print("=" * 56)

    do_lock("client_A", "file_B", ttl=4)
    do_lock("client_B", "file_B", ttl=30, wait=True)

    print("  Chờ lock của A hết hạn (4s)...")
    time.sleep(5)

    # Trigger passive expiry check qua /status
    check_status("file_B")
    time.sleep(0.1)
    check_status("file_B")

    do_unlock("client_B", "file_B")


# ─── Kịch bản 3: Renew Lock ──────────────────────────────────────────────────
def scenario_renew():
    print("\n" + "=" * 56)
    print("  Kịch bản 3: Renew Lock")
    print("  A lock TTL=5s → A renew sau 3s → lock kéo dài thêm")
    print("=" * 56)

    do_lock("client_A", "file_C", ttl=5)
    do_lock("client_B", "file_C", ttl=30, wait=True)

    print("  Chờ 3 giây rồi A renew...")
    time.sleep(3)
    do_renew("client_A", "file_C", ttl=30)

    print("  Chờ thêm 4 giây (đã qua TTL gốc 5s)...")
    time.sleep(4)
    check_status("file_C")   # A vẫn giữ lock nhờ renew

    do_unlock("client_A", "file_C")
    time.sleep(0.1)
    check_status("file_C")   # B auto-grant


# ─── Kịch bản 4: Force Unlock by Admin ───────────────────────────────────────
def scenario_force_unlock():
    print("\n" + "=" * 56)
    print("  Kịch bản 4: Force Unlock by Admin")
    print("  A lock → B chờ → admin force unlock → B auto-grant")
    print("=" * 56)

    do_lock("client_A", "file_D", ttl=60)
    do_lock("client_B", "file_D", ttl=30, wait=True)
    do_lock("client_C", "file_D", ttl=30, wait=True)

    check_status("file_D")

    do_force_unlock("hacker", "file_D")     # bị từ chối
    do_force_unlock("admin", "file_D")      # thành công

    time.sleep(0.1)
    check_status("file_D")   # B đang giữ
    do_unlock("client_B", "file_D")
    time.sleep(0.1)
    check_status("file_D")   # C đang giữ


# ─── Main ─────────────────────────────────────────────────────────────────────
SCENARIOS = {
    "queue":   scenario_queue,
    "timeout": scenario_timeout,
    "renew":   scenario_renew,
    "admin":   scenario_force_unlock,
    "all":     None,
}

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"

    try:
        requests.get(f"{BASE_URL}/locks", timeout=2)
    except Exception:
        print("Lỗi: Không kết nối được server. Hãy chạy 'python server.py' trước.")
        sys.exit(1)

    if mode == "all":
        scenario_queue()
        scenario_timeout()
        scenario_renew()
        scenario_force_unlock()
        print("\nHoàn thành mô phỏng.\n")
    elif mode in SCENARIOS:
        SCENARIOS[mode]()
        print()
    else:
        print(f"Mode không hợp lệ. Dùng: {', '.join(SCENARIOS.keys())}")
