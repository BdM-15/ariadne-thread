import { NextResponse } from "next/server";

const apiBaseUrl = process.env.ARIADNE_API_BASE_URL ?? "http://127.0.0.1:9622";

export async function POST() {
  const backendResponse = await fetch(
    `${apiBaseUrl}/mvp-2/skills-review/actions/demo-run`,
    {
      method: "POST",
      redirect: "manual",
    },
  );
  if (!backendResponse.ok && backendResponse.status !== 303) {
    return new NextResponse(await backendResponse.text(), {
      status: backendResponse.status,
    });
  }
  return NextResponse.json({ seeded: true });
}