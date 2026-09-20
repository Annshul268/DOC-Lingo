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
      <body className="antialiased bg-[#fcfdfa] dark:bg-stone-950 text-stone-900 dark:text-stone-100 selection:bg-emerald-100 selection:text-emerald-950 dark:selection:bg-emerald-900/60 dark:selection:text-emerald-200">
        {children}
      </body>
    </html>
  );
}
