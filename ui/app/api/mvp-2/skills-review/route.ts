import { NextResponse } from "next/server";

const apiBaseUrl = process.env.ARIADNE_API_BASE_URL ?? "http://127.0.0.1:9622";

export async function GET() {
  const backendResponse = await fetch(
    `${apiBaseUrl}/api/mvp-2/skills-review`,
    { cache: "no-store" },
  );
  const contentType = backendResponse.headers.get("content-type");
  const headers = new Headers();
  if (contentType !== null) {
    headers.set("content-type", contentType);
  }
  return new NextResponse(await backendResponse.text(), {
    status: backendResponse.status,
    headers,
  });
}