"""Encryption at rest: records unreadable on disk, readable through the
store, and gone for good once the person deletes their data."""
import os
import shutil
import sqlite3
import sys

TEST_DIR = "./test_data_crypto"
shutil.rmtree(TEST_DIR, ignore_errors=True)
os.environ["COPILOT_DATA_DIR"] = TEST_DIR
os.environ["CAREER_COPILOT_MASTER_KEY"] = "test-master-key"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from copilot import store  # noqa: E402

SECRET = "Cut onboarding time by 45% at Initech"


def raw_rows(user):
    conn = sqlite3.connect(os.path.join(TEST_DIR, f"{user}.db"))
    try:
        return [r[0] for r in conn.execute("SELECT body FROM records")]
    finally:
        conn.close()


def main():
    rid = store.put("u_alice", "fact", {"statement": SECRET})
    store.put("u_bob", "fact", {"statement": "Bob's fact"})
    on_disk = raw_rows("u_alice")
    assert all(r.startswith("enc:") for r in on_disk), on_disk
    assert SECRET not in " ".join(on_disk), "plain text on disk"
    keys = open(os.path.join(TEST_DIR, store.KEYS_FILE), "rb").read()
    assert b"Initech" not in keys
    print("records encrypted on disk, keys file holds no content: OK")

    assert store.get("u_alice", rid)["statement"] == SECRET
    assert store.list_kind("u_alice", "fact")[0]["statement"] == SECRET
    print("store reads them back: OK")

    # A row moved to another record id or another person won't decrypt.
    conn = sqlite3.connect(os.path.join(TEST_DIR, "u_bob.db"))
    with conn:
        conn.execute("INSERT INTO records VALUES ('stolen','fact',?,'x')",
                     (on_disk[0],))
    conn.close()
    try:
        store.get("u_bob", "stolen")
        raise AssertionError("another person's row decrypted")
    except AssertionError:
        raise
    except Exception:
        pass
    print("rows are bound to their person and record: OK")

    # Plain rows from before encryption was switched on still read.
    conn = sqlite3.connect(os.path.join(TEST_DIR, "u_alice.db"))
    with conn:
        conn.execute("INSERT INTO records VALUES ('old','fact',?,'x')",
                     ('{"statement": "older plain row"}',))
    conn.close()
    assert store.get("u_alice", "old")["statement"] == "older plain row"
    print("older plain rows still readable: OK")

    backup = os.path.join(TEST_DIR, "backup.db")
    shutil.copy(os.path.join(TEST_DIR, "u_alice.db"), backup)
    assert store.delete_all("u_alice")
    shutil.copy(backup, os.path.join(TEST_DIR, "u_alice.db"))
    store._keys.clear()                    # a fresh process, no cache
    try:
        store.get("u_alice", rid)
        raise AssertionError("backup readable after delete")
    except PermissionError:
        pass
    assert store.get("u_bob", store.list_kind("u_bob", "fact")[0]["id"]) \
        is not None, "deleting alice hurt bob"
    print("delete destroys the key, so old copies can't be read: OK")
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    print("ALL PASSED")


if __name__ == "__main__":
    main()
