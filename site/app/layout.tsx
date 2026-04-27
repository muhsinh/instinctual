import type { Metadata, Viewport } from "next";
import { GeistSans } from "geist/font/sans";
import { GeistMono } from "geist/font/mono";
import { AmbientMesh, CursorMotion } from "./components/MotionLayers";
import "./globals.css";

export const metadata: Metadata = {
  metadataBase: new URL("https://instinctual.app"),
  title: {
    default: "Instinctual — Your meetings should ship products, not tickets.",
    template: "%s — Instinctual",
  },
  description:
    "Instinctual listens to your meetings and builds the thing you're talking about while you're still talking about it. A macOS menu bar app for teams who'd rather ship than recap.",
  applicationName: "Instinctual",
  keywords: [
    "meeting AI",
    "agent orchestration",
    "macOS menu bar",
    "meeting to code",
    "Granola alternative",
    "AI for product teams",
  ],
  authors: [{ name: "Instinctual" }],
  openGraph: {
    type: "website",
    title: "Instinctual — Your meetings should ship products, not tickets.",
    description:
      "A macOS menu bar app that listens to your meetings and builds the thing you're talking about while you're still talking about it.",
    siteName: "Instinctual",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "Instinctual" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Instinctual — Your meetings should ship products, not tickets.",
    description:
      "Instinctual listens to your meetings and builds the thing you're talking about while you're still talking about it.",
    images: ["/og-image.png"],
  },
  icons: { icon: "/favicon.svg", apple: "/apple-touch-icon.png" },
};

export const viewport: Viewport = {
  themeColor: "#0c0a09",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${GeistSans.variable} ${GeistMono.variable}`}>
      <body>
        <AmbientMesh />
        <CursorMotion />
        {children}
      </body>
    </html>
  );
}
