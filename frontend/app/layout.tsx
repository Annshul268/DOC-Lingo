import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DOC-Lingo | Multilingual Document Intelligence",
  description: "Cross-lingual document retrieval and Q&A using RAG",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-blue-100 selection:text-blue-900">
        {children}
      </body>
    </html>
  );
}
