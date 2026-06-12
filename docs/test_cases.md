# Test Cases — Distributed Lock Service

## TC-01: Acquire Lock thành công

**Input:** `POST /lock` — `client_A`, `file_A`, `ttl=30`

**Kết quả mong đợi:**
```json
{ "success": true, "message": "Lock granted", "owner": "client_A" }
```

---

## TC-02: Acquire Lock bị từ chối (resource đang bị khóa)

**Điều kiện:** `file_A` đang bị `client_A` giữ

**Input:** `POST /lock` — `client_B`, `file_A`, `wait=false`

**Kết quả mong đợi:**
```json
{ "success": false, "message": "Resource is locked by another client", "owner": "client_A" }
```

---

## TC-03: Acquire Lock vào hàng đợi

**Điều kiện:** `file_A` đang bị khóa

**Input:** `POST /lock` — `client_B`, `file_A`, `wait=true`

**Kết quả mong đợi:**
```json
{ "success": false, "message": "Resource is locked. Client added to waiting queue.", "queue_position": 1 }
```

---

## TC-04: Release Lock thành công và auto-grant cho queue

**Điều kiện:** `client_A` giữ `file_A`, `client_B` đang chờ trong queue

**Input:** `POST /unlock` — `client_A`, `file_A`

**Kết quả mong đợi:**
- Unlock thành công
- `file_A` tự động cấp cho `client_B`
- Log ghi `AUTO_GRANT`

---

## TC-05: Release Lock bị từ chối (không phải owner)

**Điều kiện:** `client_A` giữ `file_A`

**Input:** `POST /unlock` — `client_B`, `file_A`

**Kết quả mong đợi:**
```json
{ "success": false, "message": "Only lock owner can unlock this resource" }
```

---

## TC-06: Lock Timeout — client khác lock được sau khi hết hạn

**Điều kiện:** `client_A` lock `file_A` TTL=5s, chờ 6s

**Input:** `POST /lock` — `client_B`, `file_A`

**Kết quả mong đợi:**
- Lock được cấp cho `client_B`
- Log ghi `EXPIRED` cho `client_A`

---

## TC-07: Lock Status — resource đang bị khóa

**Input:** `GET /status/file_A` (khi `file_A` đang bị `client_A` giữ)

**Kết quả mong đợi:**
```json
{ "status": "LOCKED", "owner": "client_A", "ttl_remaining": 25 }
```

---

## TC-08: Lock Status — resource rảnh

**Input:** `GET /status/file_A` (khi không có lock)

**Kết quả mong đợi:**
```json
{ "status": "FREE", "owner": null, "ttl_remaining": 0 }
```

---

## TC-09: Xem toàn bộ danh sách lock

**Input:** `GET /locks`

**Kết quả mong đợi:** Danh sách tất cả resource đang bị khóa với `owner`, `ttl_remaining`

---

## TC-10: Xem hàng đợi

**Input:** `GET /queue/file_A`

**Kết quả mong đợi:**
```json
{ "resource": "file_A", "queue": [{ "position": 1, "client_id": "client_B", "ttl": 30 }] }
```

---

## TC-11: Renew Lock thành công

**Điều kiện:** `client_A` giữ `file_A` TTL=10s, còn 5s

**Input:** `POST /renew` — `client_A`, `file_A`, `ttl=30`

**Kết quả mong đợi:**
```json
{ "success": true, "message": "Lock renewed", "new_expires_at": "..." }
```

---

## TC-12: Renew Lock bị từ chối (không phải owner)

**Input:** `POST /renew` — `client_B`, `file_A`

**Kết quả mong đợi:**
```json
{ "success": false, "message": "Only lock owner can renew this lock" }
```

---

## TC-13: Renew Lock đã hết hạn

**Điều kiện:** TTL đã hết

**Input:** `POST /renew` — `client_A`, `file_A`

**Kết quả mong đợi:**
```json
{ "success": false, "message": "Lock has already expired and was released" }
```

---

## TC-14: Force Unlock by Admin thành công

**Điều kiện:** `client_A` giữ `file_A`, `client_B` đang chờ queue

**Input:** `POST /admin/force-unlock` — `admin_id=admin`, `file_A`

**Kết quả mong đợi:**
- Force unlock thành công
- `client_B` tự động được cấp lock
- Log ghi `FORCE_UNLOCK` và `AUTO_GRANT`

---

## TC-15: Force Unlock bị từ chối (không phải admin)

**Input:** `POST /admin/force-unlock` — `admin_id=hacker`, `file_A`

**Kết quả mong đợi:**
```json
{ "success": false, "message": "Permission denied. Only admin can force unlock." }
```

---

## TC-16: Xem Operation Logs

**Input:** `GET /logs`

**Kết quả mong đợi:** Danh sách log đầy đủ gồm các action: `LOCK`, `UNLOCK`, `EXPIRED`, `RENEW`, `AUTO_GRANT`, `FORCE_UNLOCK`
