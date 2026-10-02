"""Run: python test_app.py  (uses a temporary database)"""
import os, tempfile, unittest, app as A

class Flow(unittest.TestCase):
    def setUp(self):
        A.DB = os.path.join(tempfile.mkdtemp(), "t.db"); A.init(); A.app.testing = True
        self.owner, self.buyer = A.app.test_client(), A.app.test_client()

    def test_full_borrow_flow(self):
        r = self.owner.post("/api/register", json={"name": "O", "email": "o@u.edu", "password": "secret1"}); self.assertEqual(r.status_code, 201)
        self.buyer.post("/api/register", json={"name": "B", "email": "b@u.edu", "password": "secret1"})
        iid = self.owner.post("/api/items", json={"title": "Calculator", "type": "borrow"}).json["id"]
        tid = self.buyer.post(f"/api/items/{iid}/request").json["id"]
        self.assertEqual(self.buyer.patch(f"/api/transactions/{tid}", json={"status": "Approved"}).status_code, 403)
        self.assertEqual(self.owner.patch(f"/api/transactions/{tid}", json={"status": "Approved"}).status_code, 200)
        self.assertEqual(self.owner.get(f"/api/items/{iid}").json["status"], "Borrowed")
        self.owner.patch(f"/api/transactions/{tid}", json={"status": "Returned"})
        self.assertEqual(self.owner.get(f"/api/items/{iid}").json["status"], "Available")

    def test_rejects_non_edu(self):
        r = self.owner.post("/api/register", json={"name": "X", "email": "x@gmail.com", "password": "secret1"})
        self.assertEqual(r.status_code, 400)

    def test_frontend_and_admin(self):
        self.assertEqual(self.owner.get("/").status_code, 200)
        self.assertEqual(self.owner.get("/api/me").status_code, 401)
        self.owner.post("/api/register", json={"name": "O", "email": "o@u.edu", "password": "secret1"})
        self.assertEqual(self.owner.get("/api/users").status_code, 403)
        self.assertEqual(self.owner.get("/api/me").json["name"], "O")

if __name__ == "__main__": unittest.main()
