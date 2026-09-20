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
      <body className="antialiased bg-[#fffdf9] dark:bg-[#141210] text-stone-900 dark:text-stone-100 selection:bg-amber-200 selection:text-amber-950 dark:selection:bg-amber-900/60 dark:selection:text-amber-200">
        {children}
      </body>
    </html>
  );
}
