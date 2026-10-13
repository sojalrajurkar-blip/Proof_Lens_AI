import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProofLens AI — Evidence-First Document Intelligence",
  description: "Investigate, retrieve, and compare documents with verifiable citations and strict proof grounding.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090d16] text-[#f8fafc] antialiased min-h-screen">
        {children}
      </body>
    </html>
  );
}
