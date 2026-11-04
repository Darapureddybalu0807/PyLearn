import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = {title:"PyPath — Python Learning Tracker",description:"Your 24-week path from Python basics to confident problem solving."};
export default function RootLayout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html>; }
