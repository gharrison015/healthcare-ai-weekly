import type { Metadata } from "next";
import { Nav } from "@/components/nav";
import "./globals.css";

export const metadata: Metadata = {
  title: "Healthcare AI Weekly",
  description:
    "Weekly intelligence on AI in healthcare. Curated for consultants, strategists, and health system leaders who need to know what matters and why.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full flex flex-col" style={{ fontFamily: "Aptos, Calibri, -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif" }}>
        <Nav />
        {children}
      </body>
    </html>
  );
}
