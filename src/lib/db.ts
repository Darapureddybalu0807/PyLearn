import { neon } from "@neondatabase/serverless";

// Lazily initialize sql client so next build doesn't throw if DATABASE_URL is missing during static analysis
export const sql = ((strings: TemplateStringsArray | string, ...values: any[]) => {
  const url = process.env.DATABASE_URL;
  if (!url) {
    throw new Error(
      "DATABASE_URL is not configured. Please add DATABASE_URL to your environment variables (e.g. in Vercel Project Settings)."
    );
  }
  const client = neon(url);
  return (client as any)(strings, ...values);
}) as ReturnType<typeof neon>;
