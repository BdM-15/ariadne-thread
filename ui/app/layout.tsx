import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Ariadne Command Center",
  description: "Production Command Center for assisted capture work.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}