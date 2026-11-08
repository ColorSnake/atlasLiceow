import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Atlas liceów — miasta Polski",
  description: "Kraków i Wrocław: mapa liceów, rankingi, zdawalność matur, historia wyników i eksport danych.",
  other: {

  },
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl">
      <body className="antialiased">{children}</body>
    </html>
  );
}
