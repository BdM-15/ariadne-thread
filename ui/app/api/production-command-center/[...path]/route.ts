import { NextRequest, NextResponse } from "next/server";

const apiBaseUrl = process.env.ARIADNE_API_BASE_URL ?? "http://127.0.0.1:9622";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

export async function GET(request: NextRequest, context: RouteContext) {
  return proxyProductionCommandCenterRequest(request, context, "GET");
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxyProductionCommandCenterRequest(request, context, "POST");
}

async function proxyProductionCommandCenterRequest(
  request: NextRequest,
  context: RouteContext,
  method: "GET" | "POST",
) {
  const params = await context.params;
  const path = params.path.map(encodeURIComponent).join("/");
  const targetUrl = new URL(`/api/production-command-center/${path}`, apiBaseUrl);
  targetUrl.search = request.nextUrl.search;

  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType !== null) {
    headers.set("content-type", contentType);
  }

  const backendResponse = await fetch(targetUrl, {
    method,
    headers,
    body: method === "POST" ? await request.text() : undefined,
    cache: "no-store",
  });
  const responseHeaders = new Headers();
  const backendContentType = backendResponse.headers.get("content-type");
  if (backendContentType !== null) {
    responseHeaders.set("content-type", backendContentType);
  }

  return new NextResponse(await backendResponse.text(), {
    status: backendResponse.status,
    headers: responseHeaders,
  });
}