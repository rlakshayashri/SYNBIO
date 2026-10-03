import React from "react";
import "./globals.css";
import { Header } from "../components/layout/Header";

export const metadata = {
  title: "SynDataX — Scientific Data Intelligence Platform",
  description: "CPU-friendly scientific data analysis, preview, and validation platform.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased">
        <Header />
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
        <footer className="border-t border-slate-900 py-6 text-center text-xs text-slate-500">
          SynDataX Scientific Platform • Modules 1 & 2 Demo • Powered by FastAPI & Next.js
        </footer>
      </body>
    </html>
  );
}
