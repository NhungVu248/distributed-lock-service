from datetime import datetime, timedelta


class LockManager:
    def __init__(self):
        self.locks = {}
        self.waiting_queues = {}
        self.logs = []

    def acquire_lock(self, client_id, resource, ttl=30, wait=False):
        # Phase 3: handle expired lock before checking if locked
        if resource in self.locks and self._is_expired(resource):
            old_owner = self.locks[resource]["owner"]
            del self.locks[resource]
            self._log(old_owner, "EXPIRED", resource, "EXPIRED", "Lock expired due to TTL")

        if resource in self.locks:
            lock = self.locks[resource]
            if wait:
                if resource not in self.waiting_queues:
                    self.waiting_queues[resource] = []
                self.waiting_queues[resource].append({
                    "client_id": client_id,
                    "ttl": ttl,
                    "requested_at": self._now()
                })
                position = len(self.waiting_queues[resource])
                self._log(client_id, "LOCK", resource, "WAITING", "Client added to waiting queue")
                return {
                    "success": False,
                    "message": "Resource is locked. Client added to waiting queue.",
                    "resource": resource,
                    "queue_position": position
                }
            else:
                ttl_remaining = self._ttl_remaining(lock)
                self._log(client_id, "LOCK", resource, "DENIED", "Resource is locked by another client")
                return {
                    "success": False,
                    "message": "Resource is locked by another client",
                    "resource": resource,
                    "owner": lock["owner"],
                    "ttl_remaining": ttl_remaining
                }

        return self._grant_lock(client_id, resource, ttl)

    def release_lock(self, client_id, resource):
        if resource not in self.locks:
            return {
                "success": False,
                "message": "Resource is not locked",
                "resource": resource
            }

        lock = self.locks[resource]
        if lock["owner"] != client_id:
            self._log(client_id, "UNLOCK", resource, "DENIED", "Only lock owner can unlock this resource")
            return {
                "success": False,
                "message": "Only lock owner can unlock this resource"
            }

        del self.locks[resource]
        self._log(client_id, "UNLOCK", resource, "SUCCESS", "Lock released")
        self._grant_next_in_queue(resource)

        return {
            "success": True,
            "message": "Lock released",
            "resource": resource
        }

    def _grant_lock(self, client_id, resource, ttl):
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl)
        self.locks[resource] = {
            "owner": client_id,
            "ttl": ttl,
            "created_at": now.strftime("%Y-%m-%d %H:%M:%S"),
            "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S")
        }
        self._log(client_id, "LOCK", resource, "SUCCESS", "Lock granted")
        return {
            "success": True,
            "message": "Lock granted",
            "resource": resource,
            "owner": client_id,
            "expires_at": self.locks[resource]["expires_at"]
        }

    def _grant_next_in_queue(self, resource):
        queue = self.waiting_queues.get(resource)
        if not queue:
            return
        next_entry = queue.pop(0)
        self._grant_lock(next_entry["client_id"], resource, next_entry["ttl"])
        self._log(next_entry["client_id"], "AUTO_GRANT", resource, "SUCCESS",
                  "Lock auto-granted from waiting queue")

    def _is_expired(self, resource):
        lock = self.locks.get(resource)
        if not lock:
            return False
        try:
            expires = datetime.strptime(lock["expires_at"], "%Y-%m-%d %H:%M:%S")
            return datetime.now() > expires
        except Exception:
            return False

    def _ttl_remaining(self, lock):
        try:
            expires = datetime.strptime(lock["expires_at"], "%Y-%m-%d %H:%M:%S")
            remaining = (expires - datetime.now()).total_seconds()
            return max(0, int(remaining))
        except Exception:
            return 0

    def _now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _log(self, client_id, action, resource, result, message):
        self.logs.append({
            "time": self._now(),
            "client_id": client_id,
            "action": action,
            "resource": resource,
            "result": result,
            "message": message
        })
