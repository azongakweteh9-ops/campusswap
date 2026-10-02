# CampusSwap: submission pack

## 1. Git commit plan
Make small commits with clear messages, in roughly this order:
1. `Add SRS and design documents`
2. `Add database schema and user registration/login`
3. `Add item CRUD and search`
4. `Add request and approval flow`
5. `Add dashboard and admin endpoints`
6. `Add front end connected to API`
7. `Add tests, README and submission notes`

Commands:
```
git init
git add .
git commit -m "Add SRS and design documents"
git remote add origin <your-repo-url>
git push -u origin main
```

## 2. Final checks (Day 9)
- [ ] `pip install -r requirements.txt` works on a clean machine
- [ ] `python test_app.py` passes
- [ ] Register two students and complete this flow in two browsers:
  list item, request, approve, mark returned
- [ ] Non-.edu email is rejected on sign up
- [ ] A second student cannot delete or approve someone else's item
- [ ] Admin login works and admin can remove a listing
- [ ] Change the default admin password and SECRET_KEY
- [ ] Pages look fine on a phone-width window

## 3. Screenshots for the report
1. Browse page with a few listings
2. Search with a category filter applied
3. Item details page
4. Add item form
5. Dashboard showing a Pending request
6. Dashboard after approval (item shows Borrowed)
7. Admin page
8. Terminal showing the tests passing
9. Use case diagram, ER diagram and status flow from the SRS

## 4. Report outline
1. Introduction and problem statement
2. Requirements (FR and NFR tables from the SRS)
3. Design: use case, ER and status diagrams, architecture
4. Implementation: tech stack, key endpoints, how roles are enforced
5. Testing: manual test table and automated tests
6. Limitations and future work (payments, chat, ratings, email verification)
7. Conclusion and team contributions

## 5. Presentation outline (about 6 slides)
1. Problem: students buy new materials they only need briefly
2. Solution and users (student, owner, admin)
3. Requirements and use cases
4. Design: ER diagram and request flow
5. Live demo (2 minutes): list, request, approve, return
6. Testing, limits and next steps

## 6. Demo script
1. Log in as Student A, add "Casio calculator" to lend.
2. In a private window, sign up as Student B, open the item, request it.
3. Back as A, open the dashboard, approve the request.
4. Show the item is now Borrowed on Browse.
5. Mark it returned and show it is Available again.
