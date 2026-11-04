# PyPath — Python Learning Tracker

A responsive Next.js app for your 24-week Python roadmap. Includes account sign-up/sign-in, a personal task list, roadmap, focus timer, study-session history and notes. Data is stored in Neon Postgres, so it follows your account across devices.

## Stack
- Next.js App Router + TypeScript
- Neon Postgres (`@neondatabase/serverless`)
- HTTP-only JWT cookie sessions (`jose`) and bcrypt password hashing
- Deployable to Vercel

## 1. Create the database
1. Create a free project at [Neon](https://neon.tech/).
2. Copy the connection string from Neon.
3. Apply the database schema in any of these ways:
   - **Using Python runner (no dependencies needed):**
     ```bash
     python database/run_schema.py "your_neon_connection_string"
     ```
   - **Using Node/npm:**
     ```bash
     npm run db:setup
     ```
   - **Neon Web Console:**
     Open the SQL Editor in your Neon dashboard, paste the contents of `database/schema.sql`, and click **Run**.

## 2. Run locally
Requirements: Node.js 20.9+ and npm.

```bash
npm install
# Add your Neon connection string to .env.local
npm run dev
```

Open http://localhost:3000. Create your account.

## 3. Deploy to Vercel
1. Create a GitHub repository and push this project.
2. In Vercel, choose **Add New → Project**, import the repository, and keep the detected Next.js settings.
3. In **Project Settings → Environment Variables**, add `DATABASE_URL` (Neon pooled URL) and `JWT_SECRET` (a long random secret). Add them for Production, Preview and Development as needed.
4. Deploy. After deployment, open the URL and create your account.

## Git commands
```bash
git init
git add .
git commit -m "Build PyPath learning tracker"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/YOUR-REPOSITORY.git
git push -u origin main
```

## Included roadmap
1. Weeks 1–4: Python foundations
2. Weeks 5–8: strings, collections, functions and recursion
3. Weeks 9–12: Big-O and core data structures/algorithms
4. Weeks 13–16: problem-solving patterns, trees and graphs
5. Weeks 17–20: OOP, files, APIs, databases and testing
6. Weeks 21–24: Git, mixed DSA, portfolio project and mock interviews

## Important notes
- Your timer runs in the browser while the page is open. Press **Save session** to store the elapsed whole minutes and notes in Neon. A paused or unsaved timer is not yet persisted.
- The roadmap is currently a built-in guide; personal tasks and study sessions are persisted per account.
- This is a learning-project starter, not a security-audited production service. Before a public launch, add rate limiting to authentication, email verification/password reset, stronger request validation, monitoring and automated tests. Use a unique `JWT_SECRET`; never commit `.env.local`.
