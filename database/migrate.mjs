import fs from "fs";
import path from "path";
import { fileURLToPath } from "url";
import { neon } from "@neondatabase/serverless";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const baseDir = path.resolve(__dirname, "..");
const schemaFile = path.join(__dirname, "schema.sql");

// Simple .env.local loader
function loadEnv() {
  const envPaths = [path.join(baseDir, ".env.local"), path.join(baseDir, ".env")];
  for (const envPath of envPaths) {
    if (fs.existsSync(envPath)) {
      const content = fs.readFileSync(envPath, "utf-8");
      for (const line of content.split("\n")) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith("#")) continue;
        const [k, ...v] = trimmed.split("=");
        if (k && v.length > 0 && !process.env[k.trim()]) {
          process.env[k.trim()] = v.join("=").trim().replace(/^['"]|['"]$/g, "");
        }
      }
    }
  }
}

loadEnv();

const dbUrl = process.argv[2] || process.env.DATABASE_URL;

if (!dbUrl || dbUrl.includes("postgresql://USER:")) {
  console.log("============================================================");
  console.log("  PyPath - Database Migration (Node.js)");
  console.log("============================================================");
  console.log("Schema file:", schemaFile);
  console.log("\n[!] No DATABASE_URL configured.");
  console.log("Provide it via command line or .env.local:");
  console.log('  node database/migrate.mjs "postgresql://..."');
  console.log("  OR set DATABASE_URL in .env.local");
  process.exit(0);
}

async function run() {
  console.log("============================================================");
  console.log("  PyPath - Executing Database Schema (Neon Postgres)");
  console.log("============================================================");
  
  const sqlContent = fs.readFileSync(schemaFile, "utf-8");
  // Clean comments and split into individual statements
  const cleanSql = sqlContent
    .replace(/--.*$/gm, "")
    .replace(/\/\*[\s\S]*?\*\//g, "");
  const statements = cleanSql
    .split(";")
    .map((s) => s.trim())
    .filter((s) => s.length > 0);

  console.log(`Found ${statements.length} SQL statements to execute.`);

  const sql = neon(dbUrl);

  for (let i = 0; i < statements.length; i++) {
    const stmt = statements[i];
    const preview = stmt.split("\n")[0].slice(0, 60);
    process.stdout.write(`[${i + 1}/${statements.length}] Running: ${preview}... `);
    try {
      await sql(stmt);
      console.log("OK");
    } catch (err) {
      console.log("FAILED");
      console.error(err.message || err);
      process.exit(1);
    }
  }

  console.log("\n[SUCCESS] All schema migrations completed successfully!");
}

run();

