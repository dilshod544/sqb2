import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IQBOL - SQB Bank AI Mentor",
  description: "SQB Bank AI Training & Exam Chatbot",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
